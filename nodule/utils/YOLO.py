from ultralytics import YOLO
import cv2
import numpy as np
import os
from django.conf import settings
model_path = os.path.join(settings.MEDIA_ROOT, 'models', 'YOLO.pt')
model = YOLO(model_path)


def convertImageCV(image):
    image_array = cv2.imdecode(np.frombuffer(image.read(), np.uint8), cv2.IMREAD_COLOR)
    gray_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    return image_array
def yoloCrop(image):
    predict=model(image)[0]
    boxes=predict.boxes
    boxData=boxes.data
    crops=[]
    for box in boxData:
        crops.append({"x":box[0],"y":box[1],"width":box[2]-box[0],"height":box[3]-box[1]})
    return crops

