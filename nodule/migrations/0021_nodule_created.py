from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def fill_created(apps, schema_editor):
    Nodule = apps.get_model("nodule", "Nodule")
    Description = apps.get_model("nodule", "Description")
    # Uploads did not store their date: use the date of their first description.
    # The public dataset (new is NULL) keeps NULL
    first_description = Description.objects.filter(nodule=OuterRef("pk")).order_by("time").values("time")[:1]
    Nodule.objects.filter(new__isnull=False).update(created=Subquery(first_description))


class Migration(migrations.Migration):

    dependencies = [
        ("nodule", "0020_nodule_declaration"),
    ]

    operations = [
        migrations.AddField(
            model_name="nodule",
            name="created",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        # Going back only needs the field removal, the data step has nothing to undo
        migrations.RunPython(fill_created, migrations.RunPython.noop),
    ]
