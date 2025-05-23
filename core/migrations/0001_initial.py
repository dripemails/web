# Generated by Django 4.2.21 on 2025-05-22 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BlogPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('summary', models.TextField(max_length=300)),
                ('content', models.TextField()),
                ('date', models.DateField(auto_now_add=True)),
                ('published', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
