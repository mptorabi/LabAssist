"""Explicit transactional writes for the supported web workflows."""
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import RecordAudit

EDITABLE = {
    'patients.patient': ('full_name', 'date_of_birth', 'sex_assigned_at_birth',
                         'height_cm', 'height_measured_on', 'weight_kg', 'weight_measured_on',
                         'medications', 'medications_as_of', 'underlying_conditions', 'conditions_as_of'),
    'labs.labreport': ('laboratory_name', 'report_number', 'report_date', 'notes',
                       'specimen', 'collection_time_text', 'received_time_text'),
    'labs.labresult': ('test_date', 'value', 'unit', 'reference_range', 'notes', 'result_kind'),
}


class StaleRecord(Exception):
    pass


def snapshot(record):
    data = {f.attname: getattr(record, f.attname) for f in record._meta.concrete_fields
            if f.name not in ('created_at', 'updated_at', 'revision', 'created_by')}
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def log(record, actor, action, reason, before):
    RecordAudit.objects.create(
        record_type=record._meta.label_lower, record_id=record.pk,
        actor=actor, actor_name=actor.get_username(), action=action,
        reason=reason, before=before, after=snapshot(record), revision=record.revision,
    )


@transaction.atomic
def create_record(record, actor):
    if record.pk or not actor.is_authenticated:
        raise ValueError('A new record and authenticated actor are required.')
    if not actor.has_perm(f'{record._meta.app_label}.add_{record._meta.model_name}'):
        raise PermissionDenied
    record.created_by = actor
    record.full_clean()
    record.save()
    log(record, actor, 'create', '', {})
    return record


@transaction.atomic
def correct_record(model, pk, revision, values, reason, actor):
    reason = reason.strip()
    if not actor.is_authenticated or not reason or len(reason) > 1000:
        raise ValidationError('A correction reason and authenticated actor are required.')
    if not actor.has_perm(f'{model._meta.app_label}.change_{model._meta.model_name}'):
        raise PermissionDenied
    allowed = EDITABLE[model._meta.label_lower]
    if set(values) - set(allowed):
        raise ValidationError('Record identities and ownership cannot be changed.')
    # Conditional UPDATE is the first database operation: unlike select_for_update,
    # this also prevents lost updates on SQLite. Audit failure rolls back this write.
    if model.objects.filter(pk=pk, revision=revision).update(revision=F('revision') + 1) != 1:
        raise StaleRecord('This record changed. Reload and compare before correcting it.')
    record = model.objects.get(pk=pk)
    before = snapshot(record)
    for name, value in values.items():
        setattr(record, name, value)
    record.full_clean()
    if snapshot(record) == before:
        raise ValidationError('No changes were supplied. Nothing was saved.')
    record.updated_at = timezone.now()
    record.save(update_fields=[*values, 'updated_at'])
    log(record, actor, 'correct', reason, before)
    return record
