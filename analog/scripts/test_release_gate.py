"""The deployed artifact must come from the revision whose quality jobs passed."""
from pathlib import Path
import unittest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[1] / '.github/workflows'


def _jobs(name):
    return yaml.load((WORKFLOWS / f'{name}.yml').read_text(encoding='utf-8'),
                     Loader=yaml.BaseLoader)['jobs']


def _step(jobs, job, prefix):
    return next(step for step in jobs[job]['steps'] if step.get('uses', '').startswith(prefix))


class ReleaseGateTests(unittest.TestCase):
    def test_deployment_requires_tests_links_and_book_at_the_same_revision(self):
        jobs = _jobs('pages')
        self.assertEqual({'tests', 'links', 'book'}, set(jobs['build']['needs']))
        self.assertEqual('build', jobs['deploy']['needs'])
        for name in ('build', 'deploy'):
            self.assertNotIn('if', jobs[name], 'Default success() gate must not be bypassed')
        for name in ('tests', 'links', 'book'):
            self.assertEqual(f'./.github/workflows/{name}.yml', jobs[name]['uses'])
            self.assertEqual("github.ref == 'refs/heads/main'", jobs[name]['if'])
            reusable = yaml.load((WORKFLOWS / f'{name}.yml').read_text(encoding='utf-8'), Loader=yaml.BaseLoader)
            self.assertIn('workflow_call', reusable['on'])
            self.assertIn('main', reusable['on']['push']['branches-ignore'])
        checkout = _step(jobs, 'build', 'actions/checkout@')
        self.assertNotIn('ref', checkout.get('with', {}), 'Do not build a newer branch head than the tested SHA')

    def test_pages_publishes_the_book_artifact_built_by_the_gated_job(self):
        jobs = _jobs('pages')
        download = _step(jobs, 'build', 'actions/download-artifact@')
        self.assertEqual('analog-circuit-book', download['with']['name'])
        self.assertEqual('analog-book/dist', download['with']['path'])
        runs = [step.get('run', '') for step in jobs['build']['steps']]
        self.assertTrue(any('scripts/publish_a4_book.py' in run for run in runs))
        upload = _step(jobs, 'build', 'actions/upload-pages-artifact@')
        self.assertEqual('build/site', upload['with']['path'])

        book_upload = _step(_jobs('book'), 'book', 'actions/upload-artifact@')
        self.assertEqual('analog-circuit-book', book_upload['with']['name'])
        self.assertEqual('analog-book/dist/', book_upload['with']['path'])

        deploy_runs = '\n'.join(step.get('run', '') for step in jobs['deploy']['steps'])
        self.assertIn('book/analog-circuit-book.html', deploy_runs)
        self.assertIn('book/analog-circuit-book.pdf', deploy_runs)
        self.assertIn('book/og-cover.png', deploy_runs)

    def test_expansion_keeps_a4_online_and_16k_draft_off_pages(self):
        pages = _jobs('pages')
        runs = "\n".join(
            step.get('run', '') for step in pages['build']['steps'])
        self.assertIn('scripts/publish_a4_book.py', runs)
        self.assertNotIn('scripts/publish_book.py', runs)
        deploy_runs = "\n".join(
            step.get('run', '') for step in pages['deploy']['steps'])
        for forbidden in ('cover.pdf', 'cover-preview.png',
                          'PRINT-SPEC.md', 'build-report.json'):
            self.assertNotIn(forbidden, deploy_runs)

        pages_text = (WORKFLOWS / 'pages.yml').read_text(encoding='utf-8')
        self.assertNotIn('book-print', pages_text,
                         '16K 失败不得阻断 A4 Pages')

        tests_runs = "\n".join(
            step.get('run', '') for job in _jobs('tests').values()
            for step in job.get('steps', []))
        self.assertIn('test_publish_a4_book.py', tests_runs)
        self.assertNotIn('test_publish_book.py', tests_runs)

        book = _jobs('book-print')
        self.assertIn('print16k', book)
        upload = _step(book, 'print16k', 'actions/upload-artifact@')
        self.assertEqual('analog-circuit-book-16k-draft',
                         upload['with']['name'])
        self.assertEqual('analog-book/dist/print/', upload['with']['path'])
        runs16 = "\n".join(
            step.get('run', '') for step in book['print16k']['steps'])
        self.assertIn('build_print_book.py', runs16)
        # 整书超过 700 页硬上限后，发布命令改为上下卷；封面/报告暂不支持 --volumes。
        for flag in ('--pdf', '--volumes'):
            self.assertIn(flag, runs16)
        workflow = yaml.load(
            (WORKFLOWS / 'book-print.yml').read_text(encoding='utf-8'),
            Loader=yaml.BaseLoader)
        self.assertNotIn('workflow_call', workflow['on'])


if __name__ == '__main__':
    unittest.main()
