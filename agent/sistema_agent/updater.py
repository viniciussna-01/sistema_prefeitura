"""Atualização automática do agente.

Consulta a versão mais recente no backend; quando houver uma versão
maior e uma URL de download configurada, baixa o novo executável e
agenda a troca na próxima reinicialização (padrão .new + script .bat,
já que o Windows não permite sobrescrever um exe em execução).
"""

import logging
import subprocess
import sys
from pathlib import Path

import httpx
from packaging.version import Version

from sistema_agent import __version__
from sistema_agent.api_client import ApiClient

logger = logging.getLogger(__name__)


def check_and_apply_update(api: ApiClient) -> bool:
    try:
        info = api.latest_version()
    except Exception:
        logger.warning("Não foi possível consultar a versão mais recente")
        return False

    latest = info.get("latest_version", "0.0.0")
    url = info.get("download_url")
    if not url or Version(latest) <= Version(__version__):
        return False

    if not getattr(sys, "frozen", False):
        logger.info("Nova versão %s disponível (executando via fonte; atualize com git pull)", latest)
        return False

    current_exe = Path(sys.executable)
    new_exe = current_exe.with_suffix(".new")
    logger.info("Baixando versão %s", latest)
    with httpx.stream("GET", url, follow_redirects=True, timeout=300) as response:
        response.raise_for_status()
        with new_exe.open("wb") as handle:
            for chunk in response.iter_bytes():
                handle.write(chunk)

    swap_script = current_exe.parent / "update_swap.bat"
    swap_script.write_text(
        "@echo off\n"
        "timeout /t 2 /nobreak > nul\n"
        f'move /y "{new_exe}" "{current_exe}"\n'
        f'start "" "{current_exe}"\n'
        "del %~f0\n",
        encoding="utf-8",
    )
    subprocess.Popen(["cmd", "/c", str(swap_script)], creationflags=0x08000000)  # CREATE_NO_WINDOW
    return True
