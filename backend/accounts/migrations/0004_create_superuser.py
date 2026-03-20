from django.db import migrations


def create_superuser(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            password='changeme',
            email='',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_telegramsubscriber'),
    ]

    operations = [
        migrations.RunPython(create_superuser, migrations.RunPython.noop),
    ]