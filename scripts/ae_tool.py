"""Run configurable AE audit/relink/queue/type-demo scripts or export only."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
from pathlib import Path

JSX = {'audit': 'audit_project.jsx', 'relink': 'relink_project.jsx',
       'queue': 'queue_export.jsx', 'type-demo': 'create_type_scene.jsx'}


def resolve_config(config: Path) -> dict:
    source = config.resolve(strict=True)
    data = json.loads(source.read_text(encoding='utf-8-sig'))
    for field in ['source_project', 'export_project', 'audit_report', 'archive_manifest', 'archived_project',
                  'render_project', 'output_video', 'type_project']:
        if field in data:
            path = Path(data[field])
            data[field] = str((source.parent/path).resolve() if not path.is_absolute() else path.resolve())
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=[*JSX, 'render'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--afterfx', default=os.environ.get('MAD_AFTERFX'))
    parser.add_argument('--aerender', default=os.environ.get('MAD_AERENDER'))
    args = parser.parse_args()
    try:
        data = resolve_config(args.config)
        if args.operation == 'render':
            if not args.aerender:
                raise ValueError('Set --aerender or MAD_AERENDER')
            project = Path(data['render_project'])
            if not project.is_file():
                raise FileNotFoundError('Run queue first; render project is missing')
            if Path(data['output_video']).exists():
                raise FileExistsError('Output video exists; choose a new path')
            command = [args.aerender, '-project', str(project), '-rqindex', '1',
                       '-sound', 'OFF', '-v', 'ERRORS_AND_PROGRESS']
            # No decoding, hashing or inspection of the output video after export.
            return subprocess.run(command, check=False).returncode
        if not args.afterfx:
            raise ValueError('Set --afterfx or MAD_AFTERFX')
        environment = os.environ.copy()
        environment['MAD_CONFIG'] = str(args.config.resolve())
        environment['MAD_OPERATION'] = args.operation
        result_fields = {'audit':['audit_report'], 'relink':['archived_project'],
                         'queue':['render_project','output_video'], 'type-demo':['type_project']}
        for field in result_fields[args.operation]:
            Path(data[field]).parent.mkdir(parents=True, exist_ok=True)
        jsx = Path(__file__).parent/'ae'/JSX[args.operation]
        status = args.config.resolve().parent/'outputs'/f'{args.operation}-status.json'
        status.parent.mkdir(parents=True, exist_ok=True)
        status.write_text(json.dumps({'state':'launching'}), encoding='utf-8')
        process = subprocess.run([args.afterfx, '-m', '-noui', '-r', str(jsx)],
                                 env=environment, check=False)
        result = json.loads(status.read_text(encoding='utf-8-sig'))
        if process.returncode or result.get('state') != 'completed':
            parser.exit(process.returncode or 1, f'AE script did not complete: {result}\n')
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    raise SystemExit(main())

