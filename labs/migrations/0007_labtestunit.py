import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labs', '0006_labtest_input_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabTestUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(help_text='Suggested unit as displayed for entry, for example: mg/dL. Not a conversion rule.', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('lab_test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suggested_units', to='labs.labtest')),
            ],
            options={
                'verbose_name': 'Lab test unit',
                'verbose_name_plural': 'Lab test units',
                'ordering': ['symbol', 'pk'],
                'constraints': [models.UniqueConstraint(fields=('lab_test', 'symbol'), name='labs_unique_test_unit')],
            },
        ),
    ]
