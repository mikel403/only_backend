from django.db import migrations


def mark_public_dataset(apps, schema_editor):
    Nodule = apps.get_model("nodule", "Nodule")
    # The public dataset (new is NULL) is public and can be used for research
    Nodule.objects.filter(new__isnull=True).update(public=True, research=True, declaration=True)


class Migration(migrations.Migration):

    dependencies = [
        ("nodule", "0021_nodule_created"),
    ]

    operations = [
        # Going back keeps the flags: they describe the dataset, they are not derived from the schema
        migrations.RunPython(mark_public_dataset, migrations.RunPython.noop),
    ]
