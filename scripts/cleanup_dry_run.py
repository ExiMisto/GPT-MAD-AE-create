"""Report unused output candidates. This program has no deletion operation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def plan(root: Path, keep: list[str]) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Root must be a directory')
    protected = set()
    for value in keep:
        path = (root / value).resolve()
        if not path.is_relative_to(root):
            raise ValueError('A keep path escapes the declared root')
        protected.add(path)
    result = []
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        actual = path.resolve()
        if not actual.is_relative_to(root):
            result.append({'path': str(path), 'action': 'protect', 'reason': 'outside-root link'})
            continue
        action = 'protect' if actual in protected else 'candidate'
        result.append({'path': str(actual), 'bytes': actual.stat().st_size, 'action': action,
                       'reason': 'explicit keep list' if action == 'protect' else
                                 'not in keep list; no dependency proof, manual review required'})
    return {'root': str(root), 'dry_run': True, 'files_removed': 0, 'entries': result,
            'candidate_bytes': sum(x.get('bytes', 0) for x in result if x['action'] == 'candidate')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--keep', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = plan(args.root, json.loads(args.keep.read_text(encoding='utf-8-sig'))['keep'])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists():
            raise FileExistsError('Plan output exists; choose a new report path')
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Dry run only; removed 0 files; report: {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

