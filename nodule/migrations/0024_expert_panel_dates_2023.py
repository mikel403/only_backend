from datetime import datetime, timedelta, timezone

from django.db import migrations

EXPERTS = ["Ana", "Dominica", "Manuela"]


def move_to_2023(apps, schema_editor):
    Description = apps.get_model("nodule", "Description")
    start = datetime(2023, 1, 1, 9, 0, tzinfo=timezone.utc)
    span = datetime(2023, 12, 31, 9, 0, tzinfo=timezone.utc) - start
    # The imported dates of the initial expert panel were wrong (2001-2031). They were all made in 2023:
    # the descriptions of each expert are spread over that year keeping their id order, which the metrics use
    for username in EXPERTS:
        descriptions = list(Description.objects.filter(user__username=username).order_by("id"))
        for i, description in enumerate(descriptions):
            description.time = start + span * i / max(len(descriptions) - 1, 1)
        Description.objects.bulk_update(descriptions, ["time"], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ("nodule", "0023_rename_physicist_physician"),
    ]

    operations = [
        # The original dates were not valid, so there is nothing to restore
        migrations.RunPython(move_to_2023, migrations.RunPython.noop),
    ]
