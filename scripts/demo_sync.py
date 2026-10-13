#!/usr/bin/env python3
"""Copia demos TF2 concluídas para data/demos sem tocar nos originais."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import os
import re
import stat
import tempfile
import time
from pathlib import Path
from typing import Callable, Mapping

LIMIT_BYTES = 2 * 1024**3
POLL_SECONDS = 2.0
GAME_PATH = Path("steamapps/common/Team Fortress 2/tf/tf2coach")


OpenChecker = Callable[..., bool]


def _normalize_vdf_path(value: str) -> Path:
    # VDF escapa barras invertidas; neste launcher, os caminhos são Linux.
    value = value.replace("\\\\", "/").replace("\\", "/")
    return Path(value).expanduser()


def parse_library_folders(library_file: Path) -> list[Path]:
    """Lê caminhos do formato atual e antigo de libraryfolders.vdf."""
    try:
        text = library_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    paths: list[Path] = []
    for raw in re.findall(r'"path"\s*"((?:\\.|[^"\\])*(?:\\.[^"\\]*)*)"', text):
        paths.append(_normalize_vdf_path(raw))

    # Formato legado: "0" "/path/to/library".
    if not paths:
        for raw in re.findall(r'^\s*"\d+"\s*"([^"\n]+)"', text, flags=re.MULTILINE):
            paths.append(_normalize_vdf_path(raw))
    return paths


def default_steam_roots(home: Path | None = None, environ: Mapping[str, str] | None = None) -> list[Path]:
    home = home or Path.home()
    environ = os.environ if environ is None else environ
    roots = []
    if environ.get("STEAM_DIR"):
        roots.append(Path(environ["STEAM_DIR"]).expanduser())
    roots.extend((home / ".steam/steam", home / ".local/share/Steam"))
    return _unique_paths(roots)


def _unique_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        try:
            key = os.path.normcase(os.fspath(path.resolve()))
        except OSError:
            key = os.path.normcase(os.path.abspath(os.fspath(path)))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def discover_demo_dirs(
    steam_roots: list[Path] | None = None,
    *,
    library_file: Path | None = None,
) -> list[Path]:
    """Retorna a pasta de demos prevista em cada biblioteca Steam conhecida."""
    roots = steam_roots if steam_roots is not None else default_steam_roots()
    libraries: list[Path] = []
    for root in roots:
        libraries.append(root)
        vdf = library_file if library_file is not None else root / "steamapps/libraryfolders.vdf"
        libraries.extend(parse_library_folders(vdf))
    return [library / GAME_PATH for library in _unique_paths(libraries)]


def _same_file_identity(a: os.stat_result, b: os.stat_result) -> bool:
    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)


def _signature(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def is_open_by_any_process(
    path: Path,
    *,
    proc_root: Path = Path("/proc"),
    ignore_pid: int | None = None,
) -> bool:
    """True se algum processo mantém o inode aberto; /proc inacessível falha fechado."""
    try:
        target = path.stat()
    except FileNotFoundError:
        return False
    target_id = (target.st_dev, target.st_ino)

    try:
        processes = list(proc_root.iterdir())
    except OSError:
        return True

    for process in processes:
        if not process.name.isdigit() or (ignore_pid is not None and int(process.name) == ignore_pid):
            continue
        fd_dir = process / "fd"
        try:
            descriptors = list(fd_dir.iterdir())
        except FileNotFoundError:
            continue  # processo encerrou durante a inspeção
        except PermissionError:
            # TF2 é iniciado pelo launcher sob o usuário atual; descritores de processos
            # alheios/ocultos não são inspecionáveis e não devem bloquear o monitor.
            continue
        except OSError:
            continue
        for descriptor in descriptors:
            try:
                opened = descriptor.stat()
            except FileNotFoundError:
                continue  # descritor fechado durante a inspeção
            except PermissionError:
                continue
            except OSError:
                continue
            if (opened.st_dev, opened.st_ino) == target_id:
                return True
    return False


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _used_bytes(directory: Path) -> int:
    if not directory.exists():
        return 0
    total = 0
    seen_inodes: set[tuple[int, int]] = set()
    for entry in directory.iterdir():
        try:
            info = entry.lstat()
        except OSError:
            continue
        identity = (info.st_dev, info.st_ino)
        if stat.S_ISREG(info.st_mode) and identity not in seen_inodes:
            seen_inodes.add(identity)
            total += info.st_size
    return total


def copy_demo(
    source: Path,
    destination_dir: Path,
    *,
    limit_bytes: int = LIMIT_BYTES,
    is_open: OpenChecker = is_open_by_any_process,
) -> str:
    """Copia um .dem concluído com SHA-256, limite e publicação sem sobrescrita."""
    source = Path(source)
    destination_dir = Path(destination_dir)
    try:
        initial = source.lstat()
    except OSError:
        return "missing"
    if source.suffix.lower() != ".dem" or not stat.S_ISREG(initial.st_mode):
        return "ignored"
    if is_open(source):
        return "open"

    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / source.name
    try:
        source_hash = _sha256_file(source)
        after_hash_stat = source.stat()
    except OSError:
        return "changed"
    if _signature(initial) != _signature(after_hash_stat):
        return "changed"
    if is_open(source):
        return "open"

    if target.exists():
        try:
            return "duplicate" if _sha256_file(target) == source_hash else "conflict"
        except OSError:
            return "conflict"

    try:
        for existing in destination_dir.glob("*.dem"):
            if existing.is_file() and _sha256_file(existing) == source_hash:
                return "duplicate"
    except OSError:
        return "conflict"

    if _used_bytes(destination_dir) + initial.st_size > limit_bytes:
        return "limit"

    temp_path: Path | None = None
    copy_digest = hashlib.sha256()
    try:
        fd, temp_name = tempfile.mkstemp(prefix=".tf2coach-", suffix=".part", dir=destination_dir)
        temp_path = Path(temp_name)
        with os.fdopen(fd, "wb") as output, source.open("rb") as input_file:
            opened_stat = os.fstat(input_file.fileno())
            if not _same_file_identity(initial, opened_stat) or _signature(initial) != _signature(opened_stat):
                return "changed"
            while True:
                chunk = input_file.read(1024 * 1024)
                if not chunk:
                    break
                # Inclui o temporário em uso; se a fonte crescer, ele também respeita o teto.
                if _used_bytes(destination_dir) + len(chunk) > limit_bytes:
                    return "limit"
                output.write(chunk)
                copy_digest.update(chunk)
            output.flush()
            os.fsync(output.fileno())
            copied_stat = os.fstat(input_file.fileno())
        if _signature(initial) != _signature(copied_stat):
            return "changed"
        if copy_digest.hexdigest() != source_hash:
            return "changed"
        if is_open(source, ignore_pid=os.getpid()):
            return "open"
        try:
            path_stat = source.stat()
        except OSError:
            return "changed"
        if _signature(initial) != _signature(path_stat):
            return "changed"
        if _sha256_file(temp_path) != source_hash or temp_path.stat().st_size != initial.st_size:
            return "integrity_error"
        if is_open(source, ignore_pid=os.getpid()):
            return "open"
        if _signature(source.stat()) != _signature(initial):
            return "changed"
        if _used_bytes(destination_dir) > limit_bytes:
            return "limit"

        try:
            os.link(temp_path, target)  # atomically refuses to replace an existing file
        except FileExistsError:
            try:
                return "duplicate" if _sha256_file(target) == source_hash else "conflict"
            except OSError:
                return "conflict"
        return "copied"
    except OSError:
        return "integrity_error"
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def sync_once(
    demo_dirs: list[Path],
    destination_dir: Path,
    *,
    limit_bytes: int = LIMIT_BYTES,
    is_open: OpenChecker = is_open_by_any_process,
    handled: dict[str, tuple[tuple[int, int, int, int, int], str]] | None = None,
) -> list[tuple[Path, str]]:
    results: list[tuple[Path, str]] = []
    for directory in demo_dirs:
        try:
            sources = sorted(directory.glob("*.dem"))
        except OSError:
            continue
        for source in sources:
            try:
                signature = _signature(source.lstat())
            except OSError:
                continue
            key = os.path.abspath(os.fspath(source))
            previous = None
            if handled is not None:
                previous = handled.get(key)
                if previous is not None and previous[0] == signature and previous[1] == "copied":
                    if not (destination_dir / source.name).exists():
                        handled.pop(key, None)
                        previous = None
            if previous is not None and previous[0] == signature:
                previous_result = previous[1]
                if previous_result != "limit" or _used_bytes(destination_dir) + signature[2] > limit_bytes:
                    results.append((source, previous_result))
                    continue
            result = copy_demo(source, destination_dir, limit_bytes=limit_bytes, is_open=is_open)
            results.append((source, result))
            if handled is not None and result in {"copied", "duplicate", "conflict", "limit"}:
                handled[key] = (signature, result)
            elif handled is not None:
                handled.pop(key, None)
    return results


def watch(
    demo_dirs: list[Path],
    destination_dir: Path,
    *,
    limit_bytes: int = LIMIT_BYTES,
    poll_seconds: float = POLL_SECONDS,
) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    lock_path = destination_dir / ".tf2coach-sync.lock"
    with lock_path.open("a") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Outro sincronizador já acompanha as demos deste repositório.", flush=True)
            return
        _watch_loop(demo_dirs, destination_dir, limit_bytes=limit_bytes, poll_seconds=poll_seconds)


def _watch_loop(
    demo_dirs: list[Path],
    destination_dir: Path,
    *,
    limit_bytes: int,
    poll_seconds: float,
) -> None:
    print("Sincronizador de demos ativo. Ctrl+C encerra; originais não serão alterados.", flush=True)
    handled: dict[str, tuple[tuple[int, int, int, int, int], str]] = {}
    warned_limit: set[str] = set()
    while True:
        for source, result in sync_once(
            demo_dirs, destination_dir, limit_bytes=limit_bytes, handled=handled
        ):
            key = os.path.abspath(os.fspath(source))
            if result == "copied":
                print("Uma demo foi copiada e verificada.", flush=True)
            elif result == "limit" and key not in warned_limit:
                warned_limit.add(key)
                print("AVISO: limite de 2 GiB atingido; novas cópias pausadas.", flush=True)
            elif result != "limit":
                warned_limit.discard(key)
        time.sleep(poll_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--demo-dir", action="append", type=Path, help="Pasta de demos (pode repetir; útil para testes)")
    parser.add_argument("--limit-bytes", type=int, default=LIMIT_BYTES, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    demo_dirs = args.demo_dir or discover_demo_dirs()
    destination_dir = args.repo_root.resolve() / "data/demos"
    try:
        watch(demo_dirs, destination_dir, limit_bytes=args.limit_bytes)
    except KeyboardInterrupt:
        print("\nSincronizador encerrado.", flush=True)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
