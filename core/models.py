from django.conf import settings
from django.db import models


class AttributedRecord(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, editable=False,
        on_delete=models.PROTECT, related_name="+",
    )
    revision = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        abstract = True


class RecordAudit(models.Model):
    """Application-managed history, not a tamper-proof database ledger."""
    record_type = models.CharField(max_length=100)
    record_id = models.PositiveBigIntegerField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    actor_name = models.CharField(max_length=255)
    occurred_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=10, choices=[('create', 'Create'), ('correct', 'Correct')])
    reason = models.CharField(max_length=1000)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    revision = models.PositiveIntegerField()

    class Meta:
        ordering = ['-occurred_at', '-pk']
        default_permissions = ('view',)
        constraints = [models.UniqueConstraint(
            fields=['record_type', 'record_id', 'revision'], name='core_unique_record_revision',
        )]
