# Generated by Django 2.1.5 on 2019-02-02 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('btc', '0002_auto_20190202_1307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='minTx',
            field=models.IntegerField(default=250),
        ),
    ]