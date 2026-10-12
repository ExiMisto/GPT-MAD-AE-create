"""Static publication file audit; no network, Git mutations or media inspection."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

TEXT_EXTENSIONS={'.md','.txt','.py','.jsx','.jsxinc','.json','.yaml','.yml','.ps1','.expr'}
MEDIA_EXTENSIONS={'.png','.jpg','.jpeg','.gif','.webp','.bmp','.tif','.tiff','.psd','.psb','.aep','.aepx',
                  '.mp4','.mkv','.mov','.avi','.webm','.mp3','.wav','.m4a','.flac','.moc3','.ttf','.otf',
                  '.exe','.dll','.jsxbin','.zip','.7z','.blend'}
GENERATED={'MANIFEST.json','RELEASE_CHECK.json'}


def audit(root: Path) -> dict:
    root=root.resolve(strict=True)
    issues=[]
    manifest=[]
    secret=re.compile(r'(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)')
    private_path=re.compile(r'(?:[A-Za-z]:[\\/](?:Users|claude_working|Adobe)[\\/]|/(?:Users|home)/)[^\n<>]*',re.I)
    for file in sorted(root.rglob('*')):
        if not file.is_file() or file.name in GENERATED or any(part in {'.git','__pycache__'} for part in file.relative_to(root).parts):
            continue
        relative=file.relative_to(root).as_posix()
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            issues.append({'file':relative,'issue':'link outside release package'})
            continue
        raw=file.read_bytes()
        manifest.append({'path':relative,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        if file.suffix.casefold() in MEDIA_EXTENSIONS:
            issues.append({'file':relative,'issue':'media/project/binary excluded from public package'})
            continue
        if len(raw)>1024*1024:
            issues.append({'file':relative,'issue':'unexpected file larger than 1 MiB'})
        if file.suffix.casefold() not in TEXT_EXTENSIONS and file.name not in {'LICENSE','.gitignore','.gitattributes'}:
            issues.append({'file':relative,'issue':'unreviewed file type'})
            continue
        try:
            text=raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            issues.append({'file':relative,'issue':'non-text content'})
            continue
        if private_path.search(text):
            issues.append({'file':relative,'issue':'private machine path'})
        if secret.search(text):
            issues.append({'file':relative,'issue':'credential-like material'})
        if file.suffix=='.md':
            for target in re.findall(r'\]\(([^)]+)\)',text):
                target=target.split('#',1)[0]
                if not target or re.match(r'^[a-z]+://',target):
                    continue
                actual=(file.parent/target).resolve()
                if not actual.is_relative_to(root) or not actual.exists():
                    issues.append({'file':relative,'issue':'broken/outside local link','target':target})
    return {'state':'passed' if not issues else 'failed','file_count':len(manifest),
            'total_bytes':sum(x['bytes'] for x in manifest),'issues':issues,'manifest':manifest,
            'scope':'Static file/link/path/credential-pattern checks only; no legal or artwork validation',
            'git_operations_executed':False,'network_publication_performed':False}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    result=audit(args.root)
    manifest=result.pop('manifest')
    (args.root/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.root/'RELEASE_CHECK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['state']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())

