# Generated by Django 4.2.7 on 2024-12-24 13:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='uploads/')),
                ('file_size', models.BigIntegerField(default=0)),
                ('encryption_key', models.BinaryField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('mime_type', models.CharField(blank=True, max_length=127)),
                ('checksum', models.CharField(blank=True, max_length=64)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='ShareLink',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.CharField(max_length=255, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_accessed', models.DateTimeField(blank=True, null=True)),
                ('access_count', models.IntegerField(default=0)),
                ('max_access_count', models.IntegerField(blank=True, null=True)),
                ('is_password_protected', models.BooleanField(default=False)),
                ('password_hash', models.CharField(blank=True, max_length=128)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_share_links', to=settings.AUTH_USER_MODEL)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='share_links', to='files.file')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FileStatistics',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('total_views', models.IntegerField(default=0)),
                ('total_downloads', models.IntegerField(default=0)),
                ('unique_visitors', models.IntegerField(default=0)),
                ('last_accessed', models.DateTimeField(blank=True, null=True)),
                ('share_count', models.IntegerField(default=0)),
                ('active_share_links', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='statistics', to='files.file')),
            ],
            options={
                'verbose_name_plural': 'File statistics',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='FileShare',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('permission', models.CharField(choices=[('view', 'View Only'), ('download', 'Download')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_accessed', models.DateTimeField(blank=True, null=True)),
                ('access_count', models.IntegerField(default=0)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shares', to='files.file')),
                ('shared_with', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FileAccess',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('accessed_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('access_type', models.CharField(choices=[('view', 'View'), ('download', 'Download')], max_length=20)),
                ('accessed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accesses', to='files.file')),
                ('share_link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='files.sharelink')),
            ],
            options={
                'ordering': ['-accessed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='sharelink',
            index=models.Index(fields=['token'], name='files_share_token_cf5ebe_idx'),
        ),
        migrations.AddIndex(
            model_name='sharelink',
            index=models.Index(fields=['created_by', 'created_at'], name='files_share_created_1b2c53_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='fileshare',
            unique_together={('file', 'shared_with')},
        ),
        migrations.AddIndex(
            model_name='fileaccess',
            index=models.Index(fields=['file', 'accessed_at'], name='files_filea_file_id_937c03_idx'),
        ),
        migrations.AddIndex(
            model_name='fileaccess',
            index=models.Index(fields=['accessed_by', 'accessed_at'], name='files_filea_accesse_3b1d2d_idx'),
        ),
    ]
