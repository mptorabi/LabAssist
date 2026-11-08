"""Upgrade rehearsal using synthetic records in Django's disposable test DB."""
from datetime import date

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class Phase2MigrationTests(TransactionTestCase):
    def test_upgrade_preserves_legacy_records_without_inventing_attribution(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        old_targets = [('core', None), ('patients', '0002_patient_sex_assigned_at_birth'),
                       ('labs', '0008_labpanel_labpanelitem')]
        try:
            executor.migrate(old_targets)
            old_apps = executor.loader.project_state([
                ('patients', '0002_patient_sex_assigned_at_birth'),
                ('labs', '0008_labpanel_labpanelitem'),
            ]).apps
            Patient = old_apps.get_model('patients', 'Patient')
            Report = old_apps.get_model('labs', 'LabReport')
            Result = old_apps.get_model('labs', 'LabResult')
            Test = old_apps.get_model('labs', 'LabTest')
            patient = Patient.objects.create(full_name='Synthetic legacy patient',
                                            date_of_birth=date(1990, 1, 1))
            test = Test.objects.create(code='SYN-MIG', name='Synthetic migration test')
            report = Report.objects.create(patient=patient, report_number='SYN-001')
            Result.objects.create(patient=patient, report=report, lab_test=test,
                                  test_date=date(2020, 1, 1), value=' <0.01 ', unit='',
                                  reference_range='', notes='Synthetic source')
            Result.objects.create(patient=patient, lab_test=test,
                                  test_date=date(2020, 1, 2), value='Negative')
            before = {name: list(model.objects.order_by('pk').values()) for name, model in
                      [('Patient', Patient), ('LabReport', Report), ('LabResult', Result)]}
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            new_apps = executor.loader.project_state(latest).apps
            for name, rows in before.items():
                model = new_apps.get_model('patients' if name == 'Patient' else 'labs', name)
                self.assertEqual(model.objects.count(), len(rows))
                for row in rows:
                    upgraded = model.objects.values().get(pk=row['id'])
                    self.assertEqual({key: upgraded[key] for key in row}, row)
                    self.assertIsNone(upgraded['created_by_id'])
                    self.assertEqual(upgraded['revision'], 0)
            self.assertEqual(new_apps.get_model('core', 'RecordAudit').objects.count(), 0)
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA integrity_check')
                self.assertEqual(cursor.fetchall(), [('ok',)])
                cursor.execute('PRAGMA foreign_key_check')
                self.assertEqual(cursor.fetchall(), [])
        finally:
            MigrationExecutor(connection).migrate(latest)
