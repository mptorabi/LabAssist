import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from labs.catalog_review import validate_proposals


class Command(BaseCommand):
    help = 'Validate a local catalog proposal file without networking or database writes.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('proposal_file')

    def handle(self, *args, **options):
        path = Path(options['proposal_file'])
        try:
            with path.open('rb') as stream:
                raw = stream.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError('File exceeds 1 MiB.')
            def unique_object(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError('Duplicate JSON key: ' + key)
                    result[key] = value
                return result
            data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object)
            errors = validate_proposals(data)
        except (OSError, ValueError, RecursionError) as exc:
            raise CommandError(str(exc)) from exc
        if errors:
            raise CommandError('\n'.join(errors))
        self.stdout.write('Structural review passed. No catalog or database changed. '
                          'Source accuracy and identity still require human verification; this is not import approval.')
