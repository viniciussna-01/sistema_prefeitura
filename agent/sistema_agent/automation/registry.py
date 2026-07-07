from sistema_agent.automation.base import PortalAdapter
from sistema_agent.automation.nfse_nacional import NfseNacionalAdapter
from sistema_agent.automation.nfse_sp import NfseSaoPauloAdapter

_ADAPTERS: dict[str, type[PortalAdapter]] = {
    "nfse_nacional": NfseNacionalAdapter,
    "nfse_sp": NfseSaoPauloAdapter,
}


def get_adapter(portal: str) -> PortalAdapter:
    adapter_cls = _ADAPTERS.get(portal)
    if adapter_cls is None:
        raise ValueError(f"Portal não suportado: {portal!r}. Disponíveis: {sorted(_ADAPTERS)}")
    return adapter_cls()


def available_portals() -> list[str]:
    return sorted(_ADAPTERS)
