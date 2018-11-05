# Generated by Django 2.0.7 on 2018-09-20 07:27

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0014_vitalquestion'),
    ]

    operations = [
        migrations.CreateModel(
            name='VitalResponse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('answer_boolean', models.NullBooleanField()),
                ('answer_time', models.TimeField(blank=True, null=True)),
                ('answer_float', models.FloatField(blank=True, null=True)),
                ('answer_integer', models.IntegerField(blank=True, null=True)),
                ('answer_scale', models.IntegerField(blank=True, null=True)),
                ('answer_string', models.CharField(blank=True, max_length=255)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='tasks.VitalQuestion')),
                ('vital_task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='tasks.VitalTask')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
