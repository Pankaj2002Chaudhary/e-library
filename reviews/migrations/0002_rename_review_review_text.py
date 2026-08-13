from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reviews", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="review",
            old_name="review",
            new_name="review_text",
        ),
    ]
