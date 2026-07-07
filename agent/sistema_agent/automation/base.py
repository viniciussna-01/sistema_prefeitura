"""Camada de abstração dos portais (padrão Adapter).

Cada portal-alvo implementa `PortalAdapter`. Se um portal passar a
oferecer API oficial autorizada, basta criar um adaptador que a consuma
(sem navegador) e registrá-lo — o restante do sistema não muda.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Page


@dataclass
class DocumentRef:
    """Referência a um documento listado no portal, antes do download."""

    document_id: str
    title: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class JobContext:
    company_name: str
    company_cnpj: str
    filters: dict[str, Any]
    log: Callable[[str], None]
    is_cancelled: Callable[[], bool]


class PortalAdapter(ABC):
    """Contrato de automação de um portal.

    O ciclo de vida é orquestrado pelo runner:
    authenticate → apply_filters → list_documents → download_document (N vezes)
    """

    #: URL usada na política de auto-seleção do certificado (padrão glob).
    certificate_url_pattern: str = "*"

    @abstractmethod
    def authenticate(self, page: Page, ctx: JobContext) -> None:
        """Autentica no portal usando o certificado digital selecionado
        (o handshake TLS é feito pelo navegador via repositório do SO)."""

    @abstractmethod
    def apply_filters(self, page: Page, ctx: JobContext) -> None:
        """Aplica período de datas e demais filtros configurados."""

    @abstractmethod
    def list_documents(self, page: Page, ctx: JobContext) -> list[DocumentRef]:
        """Lista todos os documentos encontrados (percorrendo paginação)."""

    @abstractmethod
    def download_document(self, page: Page, ctx: JobContext, doc: DocumentRef, tmp_dir: Path) -> Path:
        """Baixa UM documento para `tmp_dir` e retorna o caminho do arquivo.
        Os documentos nunca são consolidados: um arquivo por documento."""
