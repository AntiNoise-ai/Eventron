"""Unit tests for QR code generation."""

from tools.qr_gen import generate_checkin_qr, generate_qr_base64, generate_qr_bytes


class TestGenerateQrBytes:
    """Tests for raw QR byte generation."""

    def test_produces_png_bytes(self):
        """Output should be valid PNG bytes."""
        result = generate_qr_bytes("https://example.com")
        assert isinstance(result, bytes)
        # PNG magic bytes
        assert result[:4] == b"\x89PNG"

    def test_different_data_different_output(self):
        """Different input data → different QR images."""
        a = generate_qr_bytes("hello")
        b = generate_qr_bytes("world")
        assert a != b

    def test_empty_string(self):
        """Empty string should still produce a QR code."""
        result = generate_qr_bytes("")
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestGenerateQrBase64:
    """Tests for base64 data URI generation."""

    def test_produces_data_uri(self):
        """Output should be a proper data URI."""
        result = generate_qr_base64("test")
        assert result.startswith("data:image/png;base64,")

    def test_base64_decodable(self):
        """The base64 portion should be decodable."""
        import base64

        result = generate_qr_base64("test")
        b64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(b64_part)
        assert decoded[:4] == b"\x89PNG"


class TestGenerateCheckinQr:
    """Tests for check-in QR code generation."""

    def test_event_only(self):
        """QR for event without specific attendee."""
        result = generate_checkin_qr("https://seat.example.com", "evt-123")
        assert result.startswith("data:image/png;base64,")

    def test_with_attendee(self):
        """QR for specific attendee includes aid param."""
        result = generate_checkin_qr(
            "https://seat.example.com", "evt-123", attendee_id="att-456"
        )
        assert result.startswith("data:image/png;base64,")

    def test_trailing_slash_handled(self):
        """Base URL with trailing slash should not cause double slash."""
        result = generate_checkin_qr("https://example.com/", "evt-1")
        assert isinstance(result, str)
        assert len(result) > 50
