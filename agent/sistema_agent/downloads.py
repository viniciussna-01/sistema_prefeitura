"""Organização dos arquivos baixados.

Regra de negócio: cada documento permanece em um arquivo separado (nunca
consolidar em um único Excel). Estrutura:

    <downloads_dir>/<Empresa>/<arquivo>

Em caso de colisão de nomes, renomeia para:

    <Empresa>_<AAAAMMDD>_<HHMMSS>_<id>.<ext>
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def sanitize_name(name: str) -> str:
    """Remove acentos e caracteres inválidos para nomes de pasta/arquivo."""
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^\w\s.-]", "", normalized).strip()
    return re.sub(r"\s+", "_", cleaned) or "arquivo"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class StoredFile:
    file_name: str
    original_name: str
    local_path: str
    size_bytes: int
    sha256: str
    document_id: str | None = None


class DownloadOrganizer:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def company_dir(self, company_name: str) -> Path:
        directory = self.base_dir / sanitize_name(company_name)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def target_path(
        self,
        company_name: str,
        original_name: str,
        document_id: str | None = None,
        now: datetime | None = None,
    ) -> Path:
        """Calcula o destino final, renomeando automaticamente em colisões."""
        directory = self.company_dir(company_name)
        candidate = directory / sanitize_name(original_name)
        if not candidate.exists():
            return candidate

        now = now or datetime.now()
        suffix = candidate.suffix or ".bin"
        parts = [sanitize_name(company_name), now.strftime("%Y%m%d"), now.strftime("%H%M%S")]
        if document_id:
            parts.append(sanitize_name(document_id))
        renamed = directory / ("_".join(parts) + suffix)

        counter = 1
        while renamed.exists():
            renamed = directory / ("_".join(parts) + f"_{counter}" + suffix)
            counter += 1
        return renamed

    def store(
        self,
        company_name: str,
        source: Path,
        original_name: str,
        document_id: str | None = None,
        now: datetime | None = None,
    ) -> StoredFile:
        """Move o arquivo baixado (temporário do Playwright) para o destino final."""
        target = self.target_path(company_name, original_name, document_id, now)
        source.replace(target)
        return StoredFile(
            file_name=target.name,
            original_name=original_name,
            local_path=str(target),
            size_bytes=target.stat().st_size,
            sha256=sha256_of(target),
            document_id=document_id,
        )
