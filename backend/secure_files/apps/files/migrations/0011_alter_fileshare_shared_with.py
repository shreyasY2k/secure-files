# Generated by Django 4.2.7 on 2024-12-27 18:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('files', '0010_remove_file_owner_keycloak_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fileshare',
            name='shared_with',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
