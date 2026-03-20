"""QR code generation — pure function, returns image bytes or base64.

No DB, no IO beyond generating the image in memory.
"""

import base64
from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generate_qr_bytes(
    data: str,
    box_size: int = 10,
    border: int = 2,
    image_format: str = "PNG",
) -> bytes:
    """Generate a QR code image as raw bytes.

    Args:
        data: The string to encode in the QR code.
        box_size: Size of each QR module in pixels.
        border: Border width in modules.
        image_format: Output format (PNG, JPEG, etc.).

    Returns:
        Image bytes in the specified format.
    """
    qr = qrcode.QRCode(
        version=None,  # auto-detect
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format=image_format)
    return buf.getvalue()


def generate_qr_base64(
    data: str,
    box_size: int = 10,
    border: int = 2,
) -> str:
    """Generate a QR code as a base64 data URI string.

    Suitable for embedding directly in HTML <img> tags.

    Args:
        data: The string to encode.
        box_size: Size of each QR module in pixels.
        border: Border width in modules.

    Returns:
        Data URI string like 'data:image/png;base64,...'.
    """
    img_bytes = generate_qr_bytes(data, box_size=box_size, border=border)
    b64 = base64.b64encode(img_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def generate_checkin_qr(
    base_url: str,
    event_id: str,
    attendee_id: str | None = None,
) -> str:
    """Generate a check-in QR code as base64 data URI.

    Args:
        base_url: Application base URL (e.g. 'https://example.com').
        event_id: Event UUID string.
        attendee_id: Optional attendee UUID for personalized QR.

    Returns:
        Base64 data URI of the QR code image.
    """
    url = f"{base_url.rstrip('/')}/p/{event_id}/checkin"
    if attendee_id:
        url += f"?aid={attendee_id}"
    return generate_qr_base64(url)
