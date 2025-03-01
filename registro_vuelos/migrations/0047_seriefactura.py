# Generated by Django 5.1.4 on 2025-01-28 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registro_vuelos', '0046_alter_historialtransacciones_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SerieFactura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=2, unique=True)),
                ('numero_actual', models.PositiveIntegerField(default=0)),
            ],
        ),
    ]
