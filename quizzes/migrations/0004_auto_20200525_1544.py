# Generated by Django 3.0.3 on 2020-05-25 22:44

from django.db import migrations, models
import quizzes.models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0003_auto_20200525_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userresponse',
            name='response_id',
            field=models.IntegerField(default=quizzes.models.UserResponse.generate_new_id),
        ),
    ]
