import base64
import cv2
import numpy as np
from deepface import DeepFace
from docxpand.image import Image

def convertBase64ToNpArrayBGR(base64_string, img_name):
    decoded_bytes = base64.b64decode(base64_string)
    image_array = np.frombuffer(decoded_bytes, dtype=np.uint8)
    bgr_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return bgr_image

source_path = "out/img.jpg"

with open(source_path, "rb") as file:
    img1_base64 = str(base64.b64encode(file.read()).decode("utf-8"))


source_np_array = convertBase64ToNpArrayBGR(img1_base64, "src")

# image = Image.read('out/img.jpg')
analysis = DeepFace.analyze(source_np_array, actions=['emotion'], detector_backend="retinaface")
print('Anaylsis Result:', analysis)