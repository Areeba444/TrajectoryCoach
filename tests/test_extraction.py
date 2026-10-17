import csv
import gzip
import tempfile
import unittest
from pathlib import Path

from scripts.extract_subset import extract


class ExtractionTests(unittest.TestCase):
    def make_source(self, root, rows):
        path = root / 'input.csv'
        with path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['student', 'timestamp', 'eventType'])
            writer.writerows(rows)
        return path

    def test_sort_preserves_ties_source_rows_and_complete_boundary(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as folder:
            root = Path(folder)
            source = self.make_source(root, [
                [0, '2017-01-01 10:00:02', 'run'],
                [0, '2017-01-01 10:00:01', 'text_insert'],
                [0, '2017-01-01 10:00:01', 'text_remove'],
                [1, '2017-01-01 10:00:01', 'submit'],
            ])
            manifest = extract(source, root / 'output', limit=1)
            with gzip.open(root / 'output/zenodo_24_students.csv.gz', 'rt') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([r['sourceRow'] for r in rows], ['3', '4', '2'])
            self.assertEqual(manifest['events'], 3)
            self.assertEqual(manifest['students'], 1)
            self.assertEqual(manifest['raw_adjacent_timestamp_inversions'], 1)

    def test_incomplete_download_cannot_claim_complete_subset(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as folder:
            root = Path(folder)
            source = self.make_source(root, [[0, '2017-01-01 10:00:01', 'run']])
            with self.assertRaisesRegex(ValueError, 'Incomplete subset'):
                extract(source, root / 'output', limit=1)
            self.assertFalse((root / 'output/manifest.json').exists())

    def test_noncontiguous_learner_order_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as folder:
            root = Path(folder)
            source = self.make_source(root, [
                [1, '2017-01-01 10:00:01', 'run'],
                [0, '2017-01-01 10:00:02', 'run'],
            ])
            with self.assertRaisesRegex(ValueError, 'contiguous learner ordering'):
                extract(source, root / 'output', limit=2)


if __name__ == '__main__':
    unittest.main()

