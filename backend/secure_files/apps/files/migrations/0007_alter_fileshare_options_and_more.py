# Generated by Django 4.2.7 on 2024-12-26 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0006_remove_encryption_iv'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fileshare',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterUniqueTogether(
            name='fileshare',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='fileshare',
            name='keycloak_id',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='fileshare',
            name='shared_with_email',
            field=models.EmailField(default='', max_length=254),
        ),
        migrations.AddField(
            model_name='fileshare',
            name='shared_with_name',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='fileshare',
            unique_together={('file', 'keycloak_id')},
        ),
        migrations.RemoveField(
            model_name='fileshare',
            name='shared_with',
        ),
    ]
