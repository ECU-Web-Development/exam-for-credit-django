from django.db import migrations


def seed_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ('user', 'admin'):
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [('apiapp', '0003_alter_task_body_alter_task_description_notification')]
    operations = [migrations.RunPython(seed_roles, migrations.RunPython.noop)]
