# Generated by Django 5.1.1 on 2024-09-10 08:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenders', '0005_remove_tender_version_tenderversion'),
    ]

    operations = [
        migrations.CreateModel(
            name='BidVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('version', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='tenders.bid')),
            ],
            options={
                'ordering': ['-version'],
                'unique_together': {('bid', 'version')},
            },
        ),
    ]
