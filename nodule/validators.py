from django.conf import settings
from django.core.exceptions import ValidationError

#Large files make the upload and the synchronous YOLO detection slow, so they are rejected before being processed
def validate_image_size(file):
    max_size_mb=settings.MAX_UPLOAD_IMAGE_SIZE_MB
    if file.size > max_size_mb*1024*1024:
        raise ValidationError(f"Images can not be larger than {max_size_mb} MB")
