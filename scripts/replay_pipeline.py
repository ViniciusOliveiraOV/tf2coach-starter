#!/usr/bin/env python3
"""Catálogo privado de demos, análises individuais e vídeos locais."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from typing import Any
from urllib.parse import urlsplit

from scripts.analyze_demo import AnalysisError, build_analysis, render_report
from scripts.demo_sync import is_open_by_any_process


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARSER = Path("/tmp/tf-demo-parser-install/bin/parse_demo")
STEM = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\Z")
TOKEN = re.compile(r"[a-zA-Z0-9_]{1,48}\Z")
VIDEO_TYPES = {".mp4": "video/mp4", ".webm": "video/webm"}
LOCK = RLock()


class ReplayError(ValueError):
    """Entrada inválida ou arquivo privado indisponível."""


def _stem(path: Path) -> str:
    if path.suffix != ".dem" or not STEM.fullmatch(path.stem):
        raise ReplayError("A demo precisa ter nome YYYY-MM-DD_HH-MM-SS.dem.")
    try:
        datetime.strptime(path.stem, "%Y-%m-%d_%H-%M-%S")
    except ValueError as exc:
        raise ReplayError("A data no nome da demo é inválida.") from exc
    return path.stem


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_token(value: Any) -> str | None:
    return value if isinstance(value, str) and TOKEN.fullmatch(value) else None


def _safe_report(analysis: dict) -> dict:
    """Permite só os campos determinísticos aceitos pelo adaptador React."""
    return {
        "schemaVersion": 1,
        "selection": analysis["selection"],
        "map": _safe_token(analysis["map"]),
        "duration_seconds": analysis["duration_seconds"],
        "metrics": analysis["metrics"],
        "weapon_counts": {
            weapon: count for weapon, count in analysis["weapon_counts"].items()
            if _safe_token(weapon) is not None
        },
        "events": [
            {"tick": event["tick"], "roles": event["roles"],
             **({"weapon": event["weapon"]} if _safe_token(event.get("weapon")) else {})}
            for event in analysis["events"]
        ] if analysis["events"] is not None else None,
        "event_window": analysis["event_window"],
        "rounds": [
            {**({"winner": round_item["winner"]} if _safe_token(round_item.get("winner")) else {}),
             **({"length_seconds": round_item["length_seconds"]}
                if "length_seconds" in round_item else {})}
            for round_item in analysis["rounds"]
        ] if analysis["rounds"] is not None else None,
    }


def _write_new_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as output:
        output.write(data)


def _replace_json(path: Path, value: dict) -> None:
    descriptor, temp_name = tempfile.mkstemp(prefix=".replay-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        os.replace(temp_name, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _parsed_json(root: Path, stem: str, demo: Path, parser_path: Path | None) -> dict:
    destination = root / "data/parsed" / f"{stem}.json"
    if not destination.exists():
        parser = parser_path or Path(os.environ.get("TF2COACH_PARSER", DEFAULT_PARSER))
        if not parser.is_file() or not os.access(parser, os.X_OK):
            raise ReplayError("Parser ausente. Instale tf-demo-parser 0.7.1 ou informe --parser.")
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temp_name = tempfile.mkstemp(prefix=".parse-", dir=destination.parent)
        try:
            with os.fdopen(descriptor, "wb") as output:
                result = subprocess.run(
                    [str(parser), str(demo)], stdout=output, stderr=subprocess.PIPE,
                    check=False, timeout=300,
                )
            if result.returncode:
                raise ReplayError("O parser não conseguiu processar a demo.")
            parsed = json.loads(Path(temp_name).read_text(encoding="utf-8"))
            if not isinstance(parsed, dict):
                raise ReplayError("O parser não devolveu um objeto JSON.")
            os.replace(temp_name, destination)
        finally:
            Path(temp_name).unlink(missing_ok=True)
    parsed = json.loads(destination.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ReplayError("O JSON da demo precisa ser um objeto.")
    return parsed


def _video_fields(video_path: Path | None) -> dict:
    if video_path is None:
        return {"video_path": None, "video_size": None}
    video = video_path.expanduser().resolve(strict=True)
    if video.suffix.lower() not in VIDEO_TYPES or not video.is_file():
        raise ReplayError("O vídeo precisa ser um arquivo MP4 ou WebM.")
    if is_open_by_any_process(video):
        raise ReplayError("O vídeo ainda está aberto por outro processo.")
    return {"video_path": str(video), "video_size": video.stat().st_size}


def register_replay(
    root: Path,
    demo_path: Path,
    video_path: Path | None = None,
    parser_path: Path | None = None,
) -> dict:
    """Registra um par explicitamente e preserva saídas anteriores."""
    with LOCK:
        root = root.resolve()
        demo = demo_path.expanduser().resolve(strict=True)
        stem = _stem(demo)
        if not demo.is_file() or is_open_by_any_process(demo):
            raise ReplayError("A demo não está fechada e disponível.")
        demo_hash = _sha256(demo)
        destination = root / "data/replays" / f"{stem}.json"
        video = _video_fields(video_path)
        if destination.exists():
            previous = json.loads(destination.read_text(encoding="utf-8"))
            if previous.get("demo_sha256") != demo_hash:
                raise ReplayError("Já existe um replay desse nome com outra demo.")
            if previous.get("video_path") == video["video_path"] or video_path is None:
                return previous
            if previous.get("video_path") is not None:
                raise ReplayError("Já existe outro vídeo associado a esta demo.")
            updated = {**previous, **video}
            _replace_json(destination, updated)
            return updated

        analysis = build_analysis(_parsed_json(root, stem, demo, parser_path))
        markdown = render_report(analysis)
        report_path = root / "data/reports" / f"{stem}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if report_path.exists():
            if report_path.read_text(encoding="utf-8") != markdown:
                raise ReplayError("O relatório existente diverge da análise; nenhum arquivo foi substituído.")
        else:
            with report_path.open("x", encoding="utf-8") as output:
                output.write(markdown)
        record = {
            "id": stem,
            "date": datetime.strptime(stem, "%Y-%m-%d_%H-%M-%S").strftime("%d/%m/%y"),
            "demo_sha256": demo_hash,
            "report": _safe_report(analysis),
            **video,
        }
        _write_new_json(destination, record)
        return record


def unpair_replay(root: Path, demo_path: Path) -> dict:
    """Remove uma associação incorreta sem alterar a demo ou o vídeo original."""
    with LOCK:
        demo = demo_path.expanduser().resolve(strict=True)
        destination = root.resolve() / "data/replays" / f"{_stem(demo)}.json"
        record = json.loads(destination.read_text(encoding="utf-8"))
        if record.get("demo_sha256") != _sha256(demo):
            raise ReplayError("O catálogo não corresponde à demo informada.")
        updated = {**record, "video_path": None, "video_size": None}
        _replace_json(destination, updated)
        return updated


def sync_replays(root: Path, parser_path: Path | None = None) -> list[str]:
    """Processa novas demos fechadas; vídeo só é pareado por nome idêntico."""
    root = root.resolve()
    added = []
    for demo in sorted((root / "data/demos").glob("*.dem")):
        stem = _stem(demo)
        if (root / "data/replays" / f"{stem}.json").exists() or is_open_by_any_process(demo):
            continue
        videos = [root / "data/videos" / f"{stem}{extension}" for extension in VIDEO_TYPES]
        video = next((path for path in videos if path.is_file()), None)
        register_replay(root, demo, video, parser_path)
        added.append(stem)
    return added


def list_replays(root: Path) -> list[dict]:
    entries = []
    for path in sorted((root / "data/replays").glob("*.json"), reverse=True):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not STEM.fullmatch(record.get("id", "")) or path.stem != record["id"]:
            continue
        video_path = record.get("video_path")
        video_available = (
            isinstance(video_path, str) and Path(video_path).is_file()
            and Path(video_path).stat().st_size == record.get("video_size")
        )
        entries.append({
            "id": record["id"],
            "date": record["date"],
            "label": "análise gameplay",
            "report": record["report"],
            "videoUrl": f"/api/replays/{record['id']}/video" if video_available else None,
        })
    return entries


def make_server(
    root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    auto_sync: bool = True,
    parser_path: Path | None = None,
) -> ThreadingHTTPServer:
    """Serve somente o build local, o catálogo seguro e os vídeos registrados."""
    root = root.resolve()
    static_dir = root / "dist"
    if not (static_dir / "index.html").is_file():
        raise ReplayError("Build ausente. Execute npm run build antes de servir o site.")

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(static_dir), **kwargs)

        def end_headers(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            super().end_headers()

        def do_GET(self):
            route = urlsplit(self.path).path
            if route == "/api/replays":
                self._send_json(self._catalog())
                return
            if route in {"/", "/index.html"}:
                self._send_index()
                return
            match = re.fullmatch(r"/api/replays/(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})/video", route)
            if match:
                self._send_video(match.group(1))
                return
            if route.startswith("/api/"):
                self.send_error(404)
                return
            super().do_GET()

        def _catalog(self) -> dict:
            issue = None
            if auto_sync:
                try:
                    sync_replays(root, parser_path)
                except (OSError, ValueError, AnalysisError, subprocess.TimeoutExpired) as exc:
                    print(f"Falha ao atualizar catálogo local: {exc}", file=sys.stderr)
                    issue = "Uma nova demo não pôde ser processada. Consulte o terminal local."
            return {"replays": list_replays(root), "error": issue}

        def _send_index(self):
            html = (static_dir / "index.html").read_text(encoding="utf-8")
            initial = json.dumps(self._catalog(), ensure_ascii=False).replace("<", "\\u003c")
            tag = f'<script id="tf2coach-initial-catalog" type="application/json">{initial}</script>'
            encoded = html.replace("</body>", tag + "</body>").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, value: dict):
            encoded = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def _send_video(self, replay_id: str):
            record_path = root / "data/replays" / f"{replay_id}.json"
            try:
                record = json.loads(record_path.read_text(encoding="utf-8"))
                path = Path(record["video_path"])
                size = path.stat().st_size
                if (record["id"] != replay_id or path.suffix.lower() not in VIDEO_TYPES
                    or size != record["video_size"]):
                    raise ReplayError("Vídeo indisponível.")
            except (OSError, TypeError, ValueError, KeyError):
                self.send_error(404, "Vídeo indisponível")
                return

            start, end = 0, size - 1
            range_header = self.headers.get("Range")
            if range_header:
                match = re.fullmatch(r"bytes=(\d+)-(\d*)", range_header)
                if not match:
                    self.send_error(416)
                    return
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else end
                end = min(end, size - 1)
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
            self.send_response(206 if range_header else 200)
            self.send_header("Content-Type", VIDEO_TYPES[path.suffix.lower()])
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Cache-Control", "private, no-store")
            if range_header:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            with path.open("rb") as source:
                source.seek(start)
                remaining = end - start + 1
                while remaining:
                    block = source.read(min(1024 * 1024, remaining))
                    if not block:
                        break
                    try:
                        self.wfile.write(block)
                    except (BrokenPipeError, ConnectionResetError):
                        break
                    remaining -= len(block)

    return ThreadingHTTPServer((host, port), Handler)


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    register = commands.add_parser("register", help="Associa uma demo fechada a um vídeo local")
    register.add_argument("demo", type=Path)
    register.add_argument("--video", type=Path)
    register.add_argument("--parser", type=Path)
    unpair = commands.add_parser("unpair", help="Remove somente a associação de vídeo")
    unpair.add_argument("demo", type=Path)
    sync = commands.add_parser("sync", help="Processa demos novas no catálogo")
    sync.add_argument("--parser", type=Path)
    serve = commands.add_parser("serve", help="Serve o build e os vídeos somente em localhost")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--parser", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "register":
            record = register_replay(args.root, args.demo, args.video, args.parser)
            print(f"Replay registrado: {record['date']} ({record['id']}).")
        elif args.command == "unpair":
            record = unpair_replay(args.root, args.demo)
            print(f"Vídeo desassociado: {record['date']} ({record['id']}).")
        elif args.command == "sync":
            added = sync_replays(args.root, args.parser)
            print(f"Replays novos: {len(added)}.")
        else:
            server = make_server(args.root, port=args.port, parser_path=args.parser)
            print(f"Site local: http://127.0.0.1:{server.server_port}/", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
    except (OSError, ValueError, AnalysisError, json.JSONDecodeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
