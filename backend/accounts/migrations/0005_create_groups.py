from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')

    groups = [
        'Суперадмины',
        'Администраторы компаний',
        'Менеджеры',
    ]

    for name in groups:
        Group.objects.get_or_create(name=name)


def delete_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=[
        'Суперадмины',
        'Администраторы компаний',
        'Менеджеры',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_create_superuser'),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ]