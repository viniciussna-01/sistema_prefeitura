"""Ponto de entrada do agente desktop.

Roda em segundo plano com ícone na bandeja do sistema (pystray). No
primeiro uso, matricula o agente com um token gerado pelo administrador
no dashboard:

    sistema-agent --enroll <TOKEN> --api https://api.suaempresa.com.br
"""

import argparse
import logging
import platform
import sys
import threading

from sistema_agent import __version__
from sistema_agent.api_client import ApiClient
from sistema_agent.config import load_config, save_config
from sistema_agent.runner import AgentRunner
from sistema_agent.updater import check_and_apply_update

logger = logging.getLogger(__name__)


def enroll(api_url: str, token: str) -> None:
    config = load_config()
    config.api_url = api_url
    api = ApiClient(config)
    name = platform.node() or "agente"
    result = api.enroll(token, name)
    config.agent_token = result["agent_token"]
    config.agent_id = str(result["agent_id"])
    save_config(config)
    print(f"Agente matriculado com sucesso: {config.agent_id}")


def _tray_icon(runner: AgentRunner):
    """Ícone da bandeja; import tardio para permitir modo console em servidores."""
    import pystray
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (64, 64), (37, 99, 235))
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 16, 48, 48), fill=(255, 255, 255))

    def status_text(_item) -> str:
        if runner.current_job:
            return f"Executando: {runner.current_job[:8]}…"
        return "Aguardando trabalhos"

    def on_quit(icon, _item) -> None:
        runner.stop()
        icon.stop()

    return pystray.Icon(
        "sistema-prefeitura-agent",
        image,
        f"Sistema Prefeitura Agent v{__version__}",
        menu=pystray.Menu(
            pystray.MenuItem(status_text, None, enabled=False),
            pystray.MenuItem("Sair", on_quit),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Agente desktop do Sistema Prefeitura")
    parser.add_argument("--enroll", metavar="TOKEN", help="Token de matrícula gerado no dashboard")
    parser.add_argument("--api", metavar="URL", help="URL do backend (ex.: https://api.exemplo.com)")
    parser.add_argument("--console", action="store_true", help="Rodar sem ícone de bandeja")
    parser.add_argument("--headless", action="store_true", help="Navegador invisível")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    if args.enroll:
        enroll(args.api or load_config().api_url, args.enroll)
        return

    config = load_config()
    if args.api:
        config.api_url = args.api
        save_config(config)
    if args.headless:
        config.headless = True

    if not config.is_enrolled:
        print("Agente não matriculado. Gere um token no dashboard e rode:")
        print("  sistema-agent --enroll <TOKEN> --api <URL_DO_BACKEND>")
        sys.exit(1)

    runner = AgentRunner(config)
    if check_and_apply_update(runner.api):
        logger.info("Atualização em andamento; encerrando esta instância")
        return

    if args.console:
        try:
            runner.run_forever()
        except KeyboardInterrupt:
            runner.stop()
        return

    thread = threading.Thread(target=runner.run_forever, daemon=True)
    thread.start()
    _tray_icon(runner).run()


if __name__ == "__main__":
    main()
