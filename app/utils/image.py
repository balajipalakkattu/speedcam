import numpy as np
import cv2
import base64

def file_to_cv2(data):
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)
