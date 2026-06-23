import qrcode
from PIL import Image
import io
import os
import sys

# Try to import pyzbar for QR decoding
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False

# Try OpenCV
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False


def generate_qr_code(qr_id: str, product_name: str, brand_name: str) -> bytes:
    """Generate a QR code image and return as bytes."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    # Embed structured data
    data = f"ANTICOUNTERFEIT|{qr_id}|{brand_name}|{product_name}"
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a1a2e", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def decode_qr_from_image(image_bytes: bytes):
    """
    Attempt to decode QR from image bytes.
    Returns (qr_data_string, method_used) or (None, error_msg)
    """
    # Method 1: pyzbar
    if PYZBAR_AVAILABLE:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            results = pyzbar_decode(img)
            if results:
                return results[0].data.decode('utf-8'), "pyzbar"
        except Exception as e:
            pass

    # Method 2: OpenCV
    if CV2_AVAILABLE:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)
            if data:
                return data, "opencv"
        except Exception as e:
            pass

    return None, "no_decoder"


def parse_qr_data(raw_data: str):
    """
    Parse QR data string into components.
    Expected format: ANTICOUNTERFEIT|QR_ID|BRAND|PRODUCT
    """
    if raw_data and "|" in raw_data:
        parts = raw_data.split("|")
        if len(parts) >= 4 and parts[0] == "ANTICOUNTERFEIT":
            return {
                "valid_format": True,
                "qr_id": parts[1],
                "brand_name": parts[2],
                "product_name": parts[3],
                "raw": raw_data
            }
    # Could be a plain QR ID
    return {
        "valid_format": False,
        "qr_id": raw_data,
        "raw": raw_data
    }
