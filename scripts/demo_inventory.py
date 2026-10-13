#!/usr/bin/env python3
"""Inventário somente leitura de demos TF2. Não envia, modifica ou exclui arquivos."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


MAX_FILE_AGE_ACTIVE_SECONDS = 90  # Apenas heurística visual, NÃO é prova de fechamento.


def inventory(directory: Path, now: float | None = None) -> dict:
    if not directory.is_dir():
        raise NotADirectoryError(f"Diretório inexistente: {directory}")
    current_time = time.time() if now is None else now
    records = []
    for file in sorted(directory.glob('*.dem')):
        if not file.is_file() or file.is_symlink():
            continue
        metadata = file.stat()
        records.append({
            'name': file.name,
            'bytes': metadata.st_size,
            'possible_in_progress': (current_time - metadata.st_mtime) < MAX_FILE_AGE_ACTIVE_SECONDS,
            'modified_unix': metadata.st_mtime,
        })
    return {
        'directory': str(directory.resolve()),
        'count': len(records),
        'total_bytes': sum(record['bytes'] for record in records),
        'files': records,
        'warning': 'Recentidade é apenas heurística. Não usar para autorizar upload ou exclusão.',
    }


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', required=True, type=Path, help='Pasta do TF2 que contém as demos')
    parser.add_argument('--json', action='store_true', help='Emite JSON no stdout')
    args = parser.parse_args(argv)
    try:
        report = inventory(args.dir)
    except (OSError, ValueError) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    print(f"Pasta: {report['directory']}")
    print(f"Demos: {report['count']} | Total: {report['total_bytes']/1024/1024:.2f} MiB")
    for f in report['files']:
        mark = ' [talvez em gravação]' if f['possible_in_progress'] else ''
        print(f"  {f['name']}  {f['bytes']/1024/1024:.2f} MiB{mark}")
    print(report['warning'])
    return 0


if __name__ == '__main__':
    raise SystemExit(cli())
