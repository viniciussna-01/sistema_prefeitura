"""Configuração persistente do agente.

Armazenada em %APPDATA%/SistemaPrefeituraAgent/config.json (Windows) ou
~/.config/sistema-prefeitura-agent/config.json (outros sistemas, para
desenvolvimento). O token do agente é o único segredo local; a chave
privada do certificado NUNCA é tocada por este aplicativo.
"""

import json
import os
import platform
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path


def config_dir() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "SistemaPrefeituraAgent"
    return Path.home() / ".config" / "sistema-prefeitura-agent"


def default_downloads_dir() -> str:
    return str(Path.home() / "Downloads" / "SistemaPrefeitura")


@dataclass
class AgentConfig:
    api_url: str = "http://localhost:8000"
    agent_token: str = ""
    agent_id: str = ""
    machine_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    downloads_dir: str = field(default_factory=default_downloads_dir)
    poll_interval_seconds: int = 10
    heartbeat_interval_seconds: int = 30
    headless: bool = False

    @property
    def is_enrolled(self) -> bool:
        return bool(self.agent_token)


def load_config() -> AgentConfig:
    path = config_dir() / "config.json"
    if not path.exists():
        return AgentConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    known = {f for f in AgentConfig.__dataclass_fields__}
    return AgentConfig(**{k: v for k, v in data.items() if k in known})


def save_config(config: AgentConfig) -> None:
    path = config_dir() / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    if platform.system() != "Windows":
        os.chmod(path, 0o600)
