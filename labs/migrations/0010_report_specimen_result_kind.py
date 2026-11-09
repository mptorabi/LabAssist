from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labs', '0009_labreport_created_by_labreport_revision_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='labreport',
            name='collection_time_text',
            field=models.CharField(blank=True, help_text='Collection date/time exactly as printed, including timezone if supplied. No timezone is inferred.', max_length=200),
        ),
        migrations.AddField(
            model_name='labreport',
            name='received_time_text',
            field=models.CharField(blank=True, help_text='Receipt date/time exactly as printed. Leave blank if absent.', max_length=200),
        ),
        migrations.AddField(
            model_name='labreport',
            name='specimen',
            field=models.CharField(blank=True, help_text='Specimen exactly as reported; no default.', max_length=200),
        ),
        migrations.AddField(
            model_name='labresult',
            name='result_kind',
            field=models.CharField(blank=True, choices=[('', 'Not classified'), ('numeric', 'Numeric'), ('qualitative', 'Qualitative'), ('text', 'Text')], help_text='Explicit transcription classification; never inferred or used for interpretation.', max_length=16),
        ),
    ]
