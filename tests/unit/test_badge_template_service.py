"""Unit tests for BadgeTemplateService — template CRUD."""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.services.badge_template_service import BadgeTemplateService
from app.services.exceptions import TemplateNotFoundError


def _fake_template(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "name": "Standard Badge",
        "description": "Default badge layout",
        "template_type": "badge",
        "html_template": "<div>{{ name }}</div>",
        "css": "body { font-size: 14px; }",
        "preview_url": None,
        "is_builtin": False,
        "style_category": "business",
    }
    defaults.update(overrides)

    class FakeTemplate:
        pass

    obj = FakeTemplate()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


class TestBadgeTemplateServiceCreate:

    @pytest.fixture
    def repo(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, repo):
        return BadgeTemplateService(repo)

    async def test_create_defaults(self, svc, repo):
        fake = _fake_template()
        repo.create.return_value = fake
        await svc.create_template(name="Test", html_template="<div></div>")
        kw = repo.create.call_args.kwargs
        assert kw["is_builtin"] is False
        assert kw["template_type"] == "badge"
        assert kw["style_category"] == "custom"

    async def test_create_tent_card(self, svc, repo):
        fake = _fake_template(template_type="tent_card")
        repo.create.return_value = fake
        await svc.create_template(
            name="Tent", html_template="<div></div>", template_type="tent_card"
        )
        kw = repo.create.call_args.kwargs
        assert kw["template_type"] == "tent_card"


class TestBadgeTemplateServiceGet:

    @pytest.fixture
    def repo(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, repo):
        return BadgeTemplateService(repo)

    async def test_get_found(self, svc, repo):
        fake = _fake_template()
        repo.get_by_id.return_value = fake
        result = await svc.get_template(fake.id)
        assert result.name == "Standard Badge"

    async def test_get_not_found(self, svc, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TemplateNotFoundError):
            await svc.get_template(uuid.uuid4())


class TestBadgeTemplateServiceList:

    @pytest.fixture
    def repo(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, repo):
        return BadgeTemplateService(repo)

    async def test_list_all(self, svc, repo):
        repo.list_all.return_value = [_fake_template(), _fake_template()]
        result = await svc.list_templates()
        assert len(result) == 2

    async def test_list_by_type(self, svc, repo):
        repo.get_by_type.return_value = [_fake_template(template_type="tent_card")]
        result = await svc.list_templates(template_type="tent_card")
        assert len(result) == 1
        repo.get_by_type.assert_called_with("tent_card")

    async def test_list_builtins(self, svc, repo):
        repo.get_builtins.return_value = [_fake_template(is_builtin=True)]
        result = await svc.list_builtins()
        assert len(result) == 1


class TestBadgeTemplateServiceUpdate:

    @pytest.fixture
    def repo(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, repo):
        return BadgeTemplateService(repo)

    async def test_update_custom_template(self, svc, repo):
        tid = uuid.uuid4()
        repo.get_by_id.return_value = _fake_template(id=tid, is_builtin=False)
        updated = _fake_template(id=tid, name="Updated Badge")
        repo.update.return_value = updated
        result = await svc.update_template(tid, name="Updated Badge")
        assert result.name == "Updated Badge"

    async def test_update_builtin_raises(self, svc, repo):
        tid = uuid.uuid4()
        repo.get_by_id.return_value = _fake_template(id=tid, is_builtin=True)
        with pytest.raises(ValueError, match="Built-in"):
            await svc.update_template(tid, name="Hacked")

    async def test_update_not_found(self, svc, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TemplateNotFoundError):
            await svc.update_template(uuid.uuid4(), name="X")


class TestBadgeTemplateServiceDelete:

    @pytest.fixture
    def repo(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, repo):
        return BadgeTemplateService(repo)

    async def test_delete_custom(self, svc, repo):
        tid = uuid.uuid4()
        repo.get_by_id.return_value = _fake_template(id=tid, is_builtin=False)
        repo.delete.return_value = True
        result = await svc.delete_template(tid)
        assert result is True

    async def test_delete_builtin_raises(self, svc, repo):
        tid = uuid.uuid4()
        repo.get_by_id.return_value = _fake_template(id=tid, is_builtin=True)
        with pytest.raises(ValueError, match="Built-in"):
            await svc.delete_template(tid)

    async def test_delete_not_found(self, svc, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TemplateNotFoundError):
            await svc.delete_template(uuid.uuid4())
