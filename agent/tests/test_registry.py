import pytest

from sistema_agent.automation.base import PortalAdapter
from sistema_agent.automation.registry import available_portals, get_adapter


def test_available_portals():
    assert available_portals() == ["nfse_nacional", "nfse_sp"]


def test_get_adapter_returns_portal_adapter():
    for portal in available_portals():
        adapter = get_adapter(portal)
        assert isinstance(adapter, PortalAdapter)
        assert adapter.certificate_url_pattern.startswith("https://")


def test_unknown_portal_raises():
    with pytest.raises(ValueError, match="não suportado"):
        get_adapter("portal_inexistente")
