"""Copy explicitly reported assets; never remove or overwrite source files."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def archive(report: Path, output: Path) -> dict:
    report = report.resolve()
    output = output.resolve()
    data = json.loads(report.read_text(encoding='utf-8-sig'))
    rows = data.get('assets', []) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError('Report assets must be a list')
    prepared = []
    for row in rows:
        if not isinstance(row, dict) or not row.get('path'):
            raise ValueError('Every asset needs an explicit path')
        source = Path(row['path'])
        if not source.is_absolute():
            source = report.parent / source
        source = source.resolve()
        if not source.is_file():
            raise FileNotFoundError(f'Missing asset: {source}')
        if row.get('is_sequence'):
            # Single-image aliases do not prove that an entire sequence was collected.
            raise ValueError('Image sequence detected. Archive the whole sequence manually, '
                             'then import/relink as a sequence; this copier only handles explicit single files.')
        prepared.append((row, source, digest(source)))
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / 'manifest.json'
    if manifest_path.exists():
        raise FileExistsError('Archive manifest exists; choose a fresh output directory')
    files = []
    for row, source, sha in prepared:
        target = output / 'media' / (sha + source.suffix.lower())
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not target.is_file() or digest(target) != sha:
                raise FileExistsError(f'Conflicting archive target: {target}')
        else:
            shutil.copy2(source, target)
        if digest(target) != sha or source.stat().st_size != target.stat().st_size:
            raise IOError(f'Copy changed bytes: {source}')
        files.append({'original_path': str(source), 'archived_path': str(target),
                      'sha256': sha, 'bytes': target.stat().st_size,
                      'role': row.get('role', 'source'), 'is_sequence': False})
    result = {'schema': 1, 'operation': 'copy_only', 'source_report': str(report),
              'files': files, 'fonts': data.get('fonts', []) if isinstance(data, dict) else [],
              'manual_review': data.get('manual_review', []) if isinstance(data, dict) else [],
              'source_files_removed': False}
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = archive(args.report, args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(json.dumps({'copied_records': len(result['files']),
                      'unique_archive_files': len({x['archived_path'] for x in result['files']}),
                      'manifest': str(args.output.resolve() / 'manifest.json'),
                      'operation': 'copy_only'}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

