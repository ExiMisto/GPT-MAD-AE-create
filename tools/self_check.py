"""Meaningful filesystem/clock checks using generated text; no AE or media input."""
from __future__ import annotations
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def module(name):
    spec=importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    result=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(result)
    return result


archive=module('archive_assets')
dry=module('cleanup_dry_run')
frames=module('frame_plan')


class BehaviorChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def source(self,name,content):
        target=self.root/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(content,encoding='utf-8')
        return target

    def report(self,rows):
        return self.source('report.json',json.dumps({'assets':rows}))

    def test_archive_deduplicates_bytes_and_preserves_sources(self):
        a=self.source('a/placeholder.txt','self-created sample')
        b=self.source('b/placeholder.txt','self-created sample')
        before={x:archive.digest(x) for x in [a,b]}
        result=archive.archive(self.report([{'path':str(a)},{'path':str(b)}]),self.root/'archive')
        self.assertEqual(len({x['archived_path'] for x in result['files']}),1)
        self.assertEqual({x:archive.digest(x) for x in [a,b]},before)
        self.assertTrue(all(Path(x['archived_path']).read_bytes()==a.read_bytes() for x in result['files']))

    def test_same_filename_different_content_has_distinct_archived_files(self):
        a=self.source('a/placeholder.txt','first')
        b=self.source('b/placeholder.txt','second')
        result=archive.archive(self.report([{'path':str(a)},{'path':str(b)}]),self.root/'archive')
        self.assertEqual(len({x['archived_path'] for x in result['files']}),2)

    def test_missing_source_fails_before_output_created(self):
        with self.assertRaises(FileNotFoundError):
            archive.archive(self.report([{'path':'missing.txt'}]),self.root/'archive')
        self.assertFalse((self.root/'archive').exists())

    def test_image_sequence_is_not_silently_replaced_by_first_frame(self):
        source=self.source('first-frame.txt','generated placeholder')
        with self.assertRaisesRegex(ValueError,'sequence'):
            archive.archive(self.report([{'path':str(source),'is_sequence':True}]),self.root/'archive')

    def test_existing_manifest_prevents_archive_overwrite(self):
        source=self.source('source.txt','sample')
        report=self.report([{'path':str(source)}])
        output=self.root/'archive'
        archive.archive(report,output)
        before=(output/'manifest.json').read_bytes()
        with self.assertRaises(FileExistsError):
            archive.archive(report,output)
        self.assertEqual((output/'manifest.json').read_bytes(),before)

    def test_conflicting_hash_target_is_never_overwritten(self):
        source=self.source('source.txt','sample')
        output=self.root/'archive'
        conflict=self.source('archive/media/'+archive.digest(source)+'.txt','unrelated existing data')
        with self.assertRaises(FileExistsError):
            archive.archive(self.report([{'path':str(source)}]),output)
        self.assertEqual(conflict.read_text(),'unrelated existing data')

    def test_dry_run_preserves_all_files(self):
        keep=self.source('outputs/keep.txt','keep')
        old=self.source('outputs/old.txt','old')
        result=dry.plan(self.root/'outputs',['keep.txt'])
        self.assertEqual(result['files_removed'],0)
        self.assertTrue(keep.is_file() and old.is_file())
        self.assertEqual(sum(x['action']=='candidate' for x in result['entries']),1)

    def test_keep_path_cannot_escape_root(self):
        (self.root/'outputs').mkdir()
        with self.assertRaises(ValueError):
            dry.plan(self.root/'outputs',['../private.txt'])

    def test_half_open_intervals_and_fractional_fps(self):
        self.assertFalse(frames.intersection(0,1,1,2,Fraction(30))['has_frames'])
        result=frames.intersection(0,1,0,1,Fraction(30000,1001))
        self.assertEqual(result['frames'],1)
        self.assertAlmostEqual(result['duration_seconds'],1001/30000)

    def test_cli_help_is_independent_of_ae(self):
        for name in ['archive_assets','cleanup_dry_run','frame_plan','ae_tool']:
            run=subprocess.run([sys.executable,str(ROOT/'scripts'/f'{name}.py'),'--help'],
                               capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)


if __name__=='__main__':
    unittest.main(verbosity=2)

