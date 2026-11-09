import json
import tempfile
from io import StringIO
from pathlib import Path
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase
from labs.catalog_review import validate_proposals


class CatalogProposalTests(SimpleTestCase):
    # Synthetic fixtures only: these are not catalog additions or clinical sources.
    def proposal(self):
        return {'schema_version': 1, 'proposals': [{
            'code': 'SYNTHETIC', 'name': 'Synthetic only', 'specimen': '', 'method': '',
            'source_url': 'https://example.org/synthetic', 'source_title': 'Synthetic fixture',
            'source_excerpt': 'Not a clinical source', 'accessed_on': '2025-01-01',
            'reviewed_by': 'Synthetic reviewer', 'reviewed_on': '2025-01-02', 'decision': 'accepted'}]}

    def test_structure_only_without_database_access(self):
        self.assertEqual(validate_proposals(self.proposal()), [])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'proposal.json'
            path.write_text(json.dumps(self.proposal()), encoding='utf-8')
            out = StringIO()
            call_command('validate_catalog_proposals', str(path), stdout=out)
            self.assertIn('not import approval', out.getvalue())

    def test_required_evidence_and_explicit_review(self):
        for field in ['source_url', 'source_title', 'source_excerpt', 'accessed_on', 'reviewed_by', 'reviewed_on', 'decision', 'name', 'code']:
            data = self.proposal()
            data['proposals'][0][field] = ''
            self.assertTrue(validate_proposals(data), field)

    def test_rejects_invalid_shapes_duplicates_and_unsupported_fields(self):
        for data in [None, [], {}, {'schema_version': True, 'proposals': []}, {'schema_version': 1, 'proposals': []}]:
            self.assertTrue(validate_proposals(data))
        data = self.proposal()
        data['proposals'].append(dict(data['proposals'][0], code=' synthetic '))
        self.assertTrue(validate_proposals(data))
        data = self.proposal()
        data['proposals'][0]['reference_range'] = 'unsupported'
        self.assertTrue(validate_proposals(data))

    def test_invalid_source_dates_and_decision(self):
        for field, value in [('source_url', 'http://example.org'), ('source_url', 'https://user:pass@example.org'),
                             ('source_url', 'https://['), ('reviewed_on', '2024-01-01'),
                             ('reviewed_on', '2999-01-01'), ('accessed_on', 'not-a-date'),
                             ('decision', 'pending'), ('name', None)]:
            data = self.proposal()
            data['proposals'][0][field] = value
            self.assertTrue(validate_proposals(data))

    def test_command_rejects_malformed_duplicate_and_oversize_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'proposal.json'
            for text in ['{', '{"schema_version":1,"schema_version":1,"proposals":[]}', 'X' * (1024 * 1024 + 1), json.dumps(self.proposal()).replace('accepted', 'pending')]:
                path.write_text(text, encoding='utf-8')
                with self.assertRaises(CommandError):
                    call_command('validate_catalog_proposals', str(path))
