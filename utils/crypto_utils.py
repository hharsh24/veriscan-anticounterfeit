"""
crypto_utils.py
───────────────
ECDSA-P256 cryptographic signing for VeriScan QR codes.

How it works:
  1. On first run → generate a private/public key pair → save to keys/ folder
  2. When a new QR unit is created → sign the QR code string with the private key
  3. QR image embeds:  VS:<code>:<base64_signature>
  4. When customer scans → we split the string → verify signature with public key
  5. If signature is invalid → QR has been TAMPERED / CLONED → mark FAKE

Even if a counterfeiter copies the QR image pixel-for-pixel, they CANNOT create
a valid signature for a NEW serial number without the private key.
"""

import os
import base64
from pathlib import Path

KEYS_DIR = Path(__file__).parent.parent / "keys"
PRIV_KEY_PATH = KEYS_DIR / "veriscan_private.pem"
PUB_KEY_PATH  = KEYS_DIR / "veriscan_public.pem"

_private_key = None
_public_key  = None


def _ensure_keys():
    """Generate key pair on first run, load on subsequent runs."""
    global _private_key, _public_key
    if _private_key and _public_key:
        return

    try:
        from cryptography.hazmat.primitives.asymmetric.ec import (
            generate_private_key, SECP256R1
        )
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        _private_key = None
        _public_key  = None
        return

    KEYS_DIR.mkdir(exist_ok=True)

    if PRIV_KEY_PATH.exists() and PUB_KEY_PATH.exists():
        # Load existing keys
        with open(PRIV_KEY_PATH, "rb") as f:
            _private_key = serialization.load_pem_private_key(f.read(), password=None,
                                                               backend=default_backend())
        with open(PUB_KEY_PATH, "rb") as f:
            _public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
    else:
        # Generate new ECDSA P-256 key pair
        _private_key = generate_private_key(SECP256R1(), default_backend())
        _public_key  = _private_key.public_key()

        with open(PRIV_KEY_PATH, "wb") as f:
            f.write(_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(PUB_KEY_PATH, "wb") as f:
            f.write(_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))


def sign_qr_code(code: str) -> str:
    """
    Sign a QR code string with the private key.
    Returns the full QR payload:  VS:<code>:<base64sig>
    If cryptography is not installed → returns plain code (fallback).
    """
    _ensure_keys()
    if not _private_key:
        return code  # fallback: no crypto

    try:
        from cryptography.hazmat.primitives.asymmetric.ec import ECDSA
        from cryptography.hazmat.primitives import hashes

        signature = _private_key.sign(code.encode(), ECDSA(hashes.SHA256()))
        sig_b64   = base64.urlsafe_b64encode(signature).decode()
        return f"VS:{code}:{sig_b64}"
    except Exception:
        return code  # fallback


def verify_signed_qr(payload: str):
    """
    Verify a QR payload. Returns (code, is_valid, reason).

    Cases:
      payload = "VS:VS-ABCD1234:base64sig"  → verify signature → (code, True/False, reason)
      payload = "VS-ABCD1234"               → old-style plain code → (code, None, "unsigned")
      payload = anything else               → (payload, False, "unknown format")
    """
    _ensure_keys()

    # ── New signed format ──────────────────────────────────────────────────────
    if payload.startswith("VS:") and payload.count(":") >= 2:
        parts = payload.split(":", 2)
        if len(parts) == 3:
            _, code, sig_b64 = parts
            if not _public_key:
                return code, None, "crypto_unavailable"
            try:
                from cryptography.hazmat.primitives.asymmetric.ec import ECDSA
                from cryptography.hazmat.primitives import hashes
                from cryptography.exceptions import InvalidSignature

                sig = base64.urlsafe_b64decode(sig_b64 + "==")
                _public_key.verify(sig, code.encode(), ECDSA(hashes.SHA256()))
                return code, True, "signature_valid"
            except Exception:
                return code, False, "signature_invalid"

    # ── Old / plain QR code ────────────────────────────────────────────────────
    if payload.startswith("VS-"):
        return payload, None, "unsigned"

    return payload, False, "unknown_format"


def crypto_available() -> bool:
    _ensure_keys()
    return _private_key is not None
