# Generated by Django 4.2.7 on 2024-07-11 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_campaign_template'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outgoingmails',
            name='body',
        ),
        migrations.RemoveField(
            model_name='outgoingmails',
            name='subject',
        ),
        migrations.AddField(
            model_name='campaign',
            name='body',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='campaign',
            name='subject',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='outgoingmails',
            name='status',
            field=models.CharField(choices=[('queued', 'Queued'), ('sent', 'Sent'), ('failed', 'Failed')], default='queued', max_length=10),
        ),
    ]
