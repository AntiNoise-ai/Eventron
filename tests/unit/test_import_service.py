"""Unit tests for ImportService — Excel import preview + confirm."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.import_service import (
    ImportService,
    _auto_map_columns,
    _detect_duplicates,
)


# ── Pure function tests ──────────────────────────────────────

class TestAutoMapColumns:
    """Test smart field mapping from Excel headers."""

    def test_chinese_headers(self):
        mappings = _auto_map_columns(["姓名", "职位", "公司", "电话"])
        mapped = {m["excel_header"]: m["mapped_to"] for m in mappings}
        assert mapped["姓名"] == "name"
        assert mapped["职位"] == "title"
        assert mapped["公司"] == "organization"
        assert mapped["电话"] == "phone"

    def test_english_headers(self):
        mappings = _auto_map_columns(["Name", "Title", "Company", "Email"])
        mapped = {m["excel_header"]: m["mapped_to"] for m in mappings}
        assert mapped["Name"] == "name"
        assert mapped["Title"] == "title"
        assert mapped["Company"] == "organization"
        assert mapped["Email"] == "email"

    def test_unknown_header_maps_to_none(self):
        mappings = _auto_map_columns(["Random Column"])
        assert mappings[0]["mapped_to"] is None
        assert mappings[0]["confidence"] == 0.0

    def test_confidence_is_1_for_exact_match(self):
        mappings = _auto_map_columns(["姓名"])
        assert mappings[0]["confidence"] == 1.0

    def test_mixed_headers(self):
        mappings = _auto_map_columns(["参会人", "job title", "备注"])
        mapped = {m["excel_header"]: m["mapped_to"] for m in mappings}
        assert mapped["参会人"] == "name"
        assert mapped["job title"] == "title"
        assert mapped["备注"] is None


class TestDetectDuplicates:
    """Test duplicate detection logic."""

    def test_no_duplicates(self):
        rows = [{"name": "Alice"}, {"name": "Bob"}]
        warnings = _detect_duplicates(rows, set())
        assert len(warnings) == 0

    def test_internal_duplicate(self):
        rows = [{"name": "Alice"}, {"name": "Alice"}]
        warnings = _detect_duplicates(rows, set())
        assert len(warnings) == 1
        assert "duplicate" in warnings[0].lower()

    def test_existing_duplicate(self):
        rows = [{"name": "Alice"}]
        warnings = _detect_duplicates(rows, {"Alice"})
        assert len(warnings) == 1
        assert "already exists" in warnings[0]

    def test_same_name_different_org(self):
        rows = [
            {"name": "Alice", "organization": "Corp A"},
            {"name": "Alice", "organization": "Corp B"},
        ]
        warnings = _detect_duplicates(rows, set())
        assert len(warnings) == 0  # different org = not duplicate


# ── ImportService tests ──────────────────────────────────────

class TestImportService:
    """ImportService with mocked repo and excel_io."""

    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock()
        repo.get_by_event.return_value = []
        repo.create.return_value = AsyncMock()
        return repo

    @pytest.fixture
    def svc(self, mock_repo):
        return ImportService(mock_repo)

    @patch("app.services.import_service.import_attendees_from_excel")
    async def test_preview_empty_file(self, mock_parse, svc):
        mock_parse.return_value = []
        result = await svc.preview(uuid.uuid4(), b"fake")
        assert result["total_rows"] == 0
        assert "Empty" in result["warnings"][0]

    @patch("app.services.import_service.import_attendees_from_excel")
    async def test_preview_returns_mappings(self, mock_parse, svc):
        mock_parse.return_value = [
            {"姓名": "张三", "职位": "总经理"},
            {"姓名": "李四", "职位": "副总"},
        ]
        result = await svc.preview(uuid.uuid4(), b"fake")
        assert result["total_rows"] == 2
        assert len(result["column_mappings"]) == 2
        assert len(result["sample_rows"]) == 2

    @patch("app.services.import_service.import_attendees_from_excel")
    async def test_confirm_import(self, mock_parse, svc, mock_repo):
        mock_parse.return_value = [
            {"姓名": "张三", "职位": "总经理", "公司": "Acme"},
            {"姓名": "李四", "职位": "副总", "公司": "Beta"},
        ]
        result = await svc.confirm_import(
            event_id=uuid.uuid4(),
            file_bytes=b"fake",
            column_mappings={"姓名": "name", "职位": "title", "公司": "organization"},
        )
        assert result["imported_count"] == 2
        assert result["skipped_count"] == 0
        assert mock_repo.create.call_count == 2

    @patch("app.services.import_service.import_attendees_from_excel")
    async def test_confirm_skips_duplicates(self, mock_parse, svc, mock_repo):
        class FakeAttendee:
            name = "张三"
        mock_repo.get_by_event.return_value = [FakeAttendee()]
        mock_parse.return_value = [
            {"姓名": "张三", "职位": "总经理"},
            {"姓名": "李四", "职位": "副总"},
        ]
        result = await svc.confirm_import(
            event_id=uuid.uuid4(),
            file_bytes=b"fake",
            column_mappings={"姓名": "name", "职位": "title"},
            skip_duplicates=True,
        )
        assert result["imported_count"] == 1
        assert result["skipped_count"] == 1

    @patch("app.services.import_service.import_attendees_from_excel")
    async def test_confirm_nameless_row_skipped(self, mock_parse, svc, mock_repo):
        mock_parse.return_value = [{"姓名": "", "职位": "总经理"}]
        result = await svc.confirm_import(
            event_id=uuid.uuid4(),
            file_bytes=b"fake",
            column_mappings={"姓名": "name", "职位": "title"},
        )
        assert result["imported_count"] == 0
        assert result["skipped_count"] == 1
        assert len(result["errors"]) == 1
