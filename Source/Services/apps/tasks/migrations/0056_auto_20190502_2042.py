# Generated by Django 2.0.7 on 2019-05-03 02:42

from django.db import migrations


def assign_plan_templates(apps, schema_editor):
    """
    This function will iterate over all :model:`tasks.VitalTask`
    and do the following on each instance:

    - create CarePlanVitalTemplate object based on plan and
        vital_task_template
    - assign the created CarePlanVitalTemplate object above into the
        vital_template field
    """
    VitalTask = apps.get_model('tasks', 'VitalTask')
    CarePlanVitalTemplate = apps.get_model('tasks',
                                           'CarePlanVitalTemplate')
    for task in VitalTask.objects.all():
        vital_template = CarePlanVitalTemplate.objects.create(
            plan=task.plan,
            vital_task_template=task.vital_task_template
        )

        task.vital_template = vital_template
        task.save(update_fields=['[vital_template'])


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0055_vitaltask_vital_template'),
    ]

    operations = [
        migrations.RunPython(assign_plan_templates)
    ]