from django.db import migrations


def forwards(apps, schema_editor):
    Description = apps.get_model("nodule", "Description")
    ContentType = apps.get_model("contenttypes", "ContentType")

    # ContentTypes del modelo (ojo: model en minúsculas)
    ct_physicist = ContentType.objects.get(app_label="nodule", model="physicist")
    ct_testuser = ContentType.objects.get(app_label="nodule", model="testuser")
    ct_ai = ContentType.objects.get(app_label="nodule", model="ai")

    # Recorremos en streaming por si hay muchas filas
    qs = Description.objects.all().only("id", "content_type_id", "object_id", "user_id", "ai_id")
    for d in qs.iterator():
        # Si ya está migrado, saltar
        if d.user_id or d.ai_id:
            continue

        if d.content_type_id == ct_ai.id:
            # object_id -> AI.id
            d.ai_id = d.object_id
            d.user_id = None
            d.save(update_fields=["ai", "user"])

        elif d.content_type_id in (ct_physicist.id, ct_testuser.id):
            # object_id -> User.id (porque Physicist/TestUser tienen pk=user_id)
            d.user_id = d.object_id
            d.ai_id = None
            d.save(update_fields=["user", "ai"])

        else:
            # Si hubiera otros tipos, los dejamos intactos
            continue


def backwards(apps, schema_editor):
    # Opcional: “des-migrar” (aquí lo dejamos sin hacer para evitar errores)
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("nodule", "0009_description_ai_description_user"),  # <-- CAMBIA ESTO por tu migración anterior real
        ("contenttypes", "__latest__"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]