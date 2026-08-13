import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reviews", "0002_rename_review_review_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="review",
            name="rating",
            field=models.PositiveSmallIntegerField(),
        ),
        migrations.AlterField(
            model_name="review",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
