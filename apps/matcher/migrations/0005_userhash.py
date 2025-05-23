# Generated by Django 4.2.9 on 2025-04-29 13:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matcher', '0004_rename_speech_embedding_userspeech_embedding_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserHash',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='matcher.userspeech')),
                ('hash_value', models.BigIntegerField()),
            ],
        ),
    ]
