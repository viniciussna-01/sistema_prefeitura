"""Preparação do navegador para autenticação com certificado digital.

Estratégia: usar o canal Microsoft Edge/Chrome do Playwright, que no
Windows consulta o repositório de certificados do sistema (incluindo
tokens A3 via CSP/KSP). Para evitar o diálogo nativo de seleção — que o
Playwright não consegue clicar — gravamos a política
`AutoSelectCertificateForUrls` no registro (HKCU), restrita à URL do
portal e ao certificado escolhido pelo usuário. A política é removida ao
final da execução.

A chave privada nunca é lida por este código: o handshake TLS mútuo é
feito pelo próprio navegador usando as APIs do Windows.
"""

import json
import platform
from contextlib import contextmanager

EDGE_POLICY_KEY = r"Software\Policies\Microsoft\Edge"
CHROME_POLICY_KEY = r"Software\Policies\Google\Chrome"
POLICY_VALUE_NAME = "AutoSelectCertificateForUrls"


def _policy_entry(url_pattern: str, issuer_cn: str | None = None) -> str:
    cert_filter: dict = {}
    if issuer_cn:
        cert_filter = {"ISSUER": {"CN": issuer_cn}}
    return json.dumps({"pattern": url_pattern, "filter": cert_filter})


@contextmanager
def auto_select_certificate(url_pattern: str, issuer_cn: str | None = None):
    """Aplica temporariamente a política de seleção automática de certificado."""
    if platform.system() != "Windows":
        yield
        return

    import winreg

    entry = _policy_entry(url_pattern, issuer_cn)
    written: list[tuple[str, str]] = []
    for base_key in (EDGE_POLICY_KEY, CHROME_POLICY_KEY):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{base_key}\\{POLICY_VALUE_NAME}")
            winreg.SetValueEx(key, "1", 0, winreg.REG_SZ, entry)
            winreg.CloseKey(key)
            written.append((base_key, POLICY_VALUE_NAME))
        except OSError:
            continue
    try:
        yield
    finally:
        for base_key, value_name in written:
            try:
                winreg.DeleteKey(
                    winreg.HKEY_CURRENT_USER, f"{base_key}\\{value_name}"
                )
            except OSError:
                pass


def launch_browser(playwright, headless: bool = False):
    """Abre o navegador preferindo canais que integram com o repositório
    de certificados do Windows (Edge, depois Chrome, por fim Chromium)."""
    for channel in ("msedge", "chrome"):
        try:
            return playwright.chromium.launch(channel=channel, headless=headless)
        except Exception:
            continue
    return playwright.chromium.launch(headless=headless)
