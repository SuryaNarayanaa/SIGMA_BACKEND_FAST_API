import base64
import cv2
import numpy as np


def readb64(uri):
    encoded_data = uri.split(",")[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def qr_decoder(image):
    # Initialize the QRCode detector
    detector = cv2.QRCodeDetector()

    # Detect and decode the QR code
    data, vertices_array, _ = detector.detectAndDecode(image)

    if vertices_array is not None and data:
        return data  # Return the decoded data as a string

    raise ValueError("No QR code found in the image.")