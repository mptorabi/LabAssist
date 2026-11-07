"""Regression tests for private local configuration; no patient database access."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.local_config import load_debug, load_secret_key
from config.local_setup import initialize


class LocalConfigurationTests(SimpleTestCase):
    def test_setup_creates_valid_stable_key(self):
        with TemporaryDirectory() as directory:
            self.assertTrue(initialize(directory))
            key = load_secret_key(directory, {})
            self.assertGreaterEqual(len(key), 50)
            self.assertFalse(initialize(directory))
            self.assertEqual(load_secret_key(directory, {}), key)
            self.assertEqual(list(Path(directory).iterdir()), [Path(directory) / '.local'])

    def test_separate_installations_have_different_keys(self):
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            initialize(first)
            initialize(second)
            self.assertNotEqual(load_secret_key(first, {}), load_secret_key(second, {}))

    def test_missing_key_fails_without_creating_files(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesMessage(ImproperlyConfigured, 'python -m config.local_setup'):
                load_secret_key(directory, {})
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_environment_key_takes_precedence(self):
        with TemporaryDirectory() as directory:
            initialize(directory)
            key = 'abcdef0123456789' * 5
            self.assertEqual(load_secret_key(directory, {'LABASSIST_SECRET_KEY': key}), key)

    def test_invalid_keys_are_rejected(self):
        for key in ['', 'short', 'a' * 70, 'django-insecure-' + 'abcdef123456' * 6]:
            with self.subTest(key=key), self.assertRaises(ImproperlyConfigured):
                load_secret_key('.', {'LABASSIST_SECRET_KEY': key})

    def test_invalid_environment_key_does_not_fall_back(self):
        with TemporaryDirectory() as directory:
            initialize(directory)
            with self.assertRaises(ImproperlyConfigured):
                load_secret_key(directory, {'LABASSIST_SECRET_KEY': ''})

    def test_existing_invalid_file_is_not_overwritten(self):
        with TemporaryDirectory() as directory:
            initialize(directory)
            path = Path(directory) / '.local' / 'secret_key'
            path.write_text('bad', encoding='utf-8')
            self.assertFalse(initialize(directory))
            self.assertEqual(path.read_text(encoding='utf-8'), 'bad')
            with self.assertRaises(ImproperlyConfigured):
                load_secret_key(directory, {})

    def test_debug_defaults_to_false(self):
        self.assertFalse(load_debug({}))

    def test_explicit_debug_values(self):
        for value, expected in [('true', True), ('1', True), (' TRUE ', True),
                                ('false', False), ('0', False)]:
            with self.subTest(value=value):
                self.assertEqual(load_debug({'LABASSIST_DEBUG': value}), expected)

    def test_invalid_debug_fails_closed(self):
        for value in ['', 'yes', 'tru']:
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                load_debug({'LABASSIST_DEBUG': value})

    def test_real_environment_is_supported(self):
        with patch.dict('os.environ', {'LABASSIST_DEBUG': 'false',
                                     'LABASSIST_SECRET_KEY': 'abcdef1234567890' * 5}):
            self.assertFalse(load_debug())
            self.assertEqual(load_secret_key('.'), 'abcdef1234567890' * 5)
