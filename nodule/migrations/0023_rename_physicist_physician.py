from django.db import migrations


def rename_permissions(apps, schema_editor, old="physicist", new="physician"):
    # Keeps the permissions already given to users and groups (add_physicist -> add_physician...)
    Permission = apps.get_model("auth", "Permission")
    for permission in Permission.objects.filter(content_type__app_label="nodule", codename__endswith=f"_{old}"):
        permission.codename = permission.codename[: -len(old)] + new
        permission.name = permission.name.replace(old, new)
        permission.save(update_fields=["codename", "name"])


def restore_permissions(apps, schema_editor):
    rename_permissions(apps, schema_editor, old="physician", new="physicist")


class Migration(migrations.Migration):

    dependencies = [
        ("nodule", "0022_public_dataset_flags"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        # Renames the table (nodule_physicist -> nodule_physician) keeping its rows; contenttypes renames its entry too
        migrations.RenameModel(old_name="Physicist", new_name="Physician"),
        migrations.RunPython(rename_permissions, restore_permissions),
    ]
