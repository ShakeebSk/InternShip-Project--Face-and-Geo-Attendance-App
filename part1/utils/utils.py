import base64
from PIL import Image
import numpy as np
import io
import cv2
import face_recognition

# def decode_base64_image(base64_string):
#     """
#     Converts base64 → RGB numpy image
#     """
#     if "," in base64_string:
#         base64_string = base64_string.split(",")[1]

#     image_bytes = base64.b64decode(base64_string)
#     image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     return np.array(image)


def decode_base64_image(data_url):
    try:
        header, encoded = data_url.split(",", 1)

        # Fix padding
        missing_padding = len(encoded) % 4
        if missing_padding:
            encoded += "=" * (4 - missing_padding)

        img_bytes = base64.b64decode(encoded)

        np_arr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        return image  # BGR image for OpenCV

    except Exception as e:
        print("Decode error:", e)
        return None


def get_face_encoding(img_rgb):
    """
    Returns 128-d face encoding or None
    """
    boxes = face_recognition.face_locations(img_rgb)

    if len(boxes) == 0:
        return None

    encodings = face_recognition.face_encodings(img_rgb, boxes)

    return encodings[0] if encodings else None


def compare_encodings(known_enc, new_enc):
    import numpy as np
    dist = np.linalg.norm(np.array(known_enc) - np.array(new_enc))
    return dist
