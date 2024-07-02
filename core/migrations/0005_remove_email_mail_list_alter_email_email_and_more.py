# Generated by Django 5.0.6 on 2024-07-01 11:36

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_email_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='email',
            name='mail_list',
        ),
        migrations.AlterField(
            model_name='email',
            name='email',
            field=models.EmailField(max_length=254, unique=True, validators=[django.core.validators.EmailValidator()]),
        ),
        migrations.CreateModel(
            name='EmailMailList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('unsubscribed_at', models.DateTimeField(blank=True, null=True)),
                ('email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.email')),
                ('mail_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.maillist')),
            ],
            options={
                'unique_together': {('email', 'mail_list')},
            },
        ),
    ]
