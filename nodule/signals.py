from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Nodule


#Django does not remove files when a row is deleted, so the images of a deleted nodule are removed here
@receiver(post_delete, sender=Nodule)
def delete_nodule_files(sender, instance, **kwargs):
    for field in (instance.image, instance.full_image):
        if not field:
            continue
        name, storage = field.name, field.storage

        def remove(name=name, storage=storage):
            # Only once the deletion is committed, and never a file still used by another nodule
            if not Nodule.objects.filter(Q(image=name) | Q(full_image=name)).exists():
                storage.delete(name)

        transaction.on_commit(remove)
