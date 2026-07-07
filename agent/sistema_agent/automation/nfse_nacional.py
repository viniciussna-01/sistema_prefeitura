"""Adaptador do Emissor Nacional de NFS-e (www.nfse.gov.br).

ATENÇÃO: os seletores abaixo refletem a estrutura do portal e devem ser
revisados quando o portal mudar. Toda a lógica específica do portal vive
apenas neste arquivo — o restante do sistema é agnóstico.
"""

from pathlib import Path

from playwright.sync_api import Page

from sistema_agent.automation.base import DocumentRef, JobContext, PortalAdapter

BASE_URL = "https://www.nfse.gov.br/EmissorNacional"


class NfseNacionalAdapter(PortalAdapter):
    certificate_url_pattern = "https://www.nfse.gov.br"

    def authenticate(self, page: Page, ctx: JobContext) -> None:
        ctx.log("Abrindo o Emissor Nacional de NFS-e")
        page.goto(f"{BASE_URL}/Login", wait_until="domcontentloaded")

        # Botão "Entrar com certificado digital" — o navegador seleciona o
        # certificado automaticamente via política AutoSelectCertificateForUrls.
        page.get_by_role("link", name="Certificado Digital").or_(
            page.get_by_role("button", name="Certificado Digital")
        ).first.click()
        page.wait_for_load_state("networkidle")

        if "Login" in page.url:
            raise RuntimeError("Autenticação com certificado digital falhou no portal nacional")
        ctx.log("Autenticado com certificado digital")

    def apply_filters(self, page: Page, ctx: JobContext) -> None:
        start = ctx.filters["start_date"]
        end = ctx.filters["end_date"]
        ctx.log(f"Aplicando filtro de período: {start} a {end}")

        page.goto(f"{BASE_URL}/Notas/Emitidas", wait_until="domcontentloaded")
        page.fill("input[name='DataInicial']", _to_br_date(start))
        page.fill("input[name='DataFinal']", _to_br_date(end))
        for key, value in ctx.filters.get("extra", {}).items():
            locator = page.locator(f"[name='{key}']")
            if locator.count():
                locator.first.fill(str(value))
        page.get_by_role("button", name="Pesquisar").click()
        page.wait_for_load_state("networkidle")

    def list_documents(self, page: Page, ctx: JobContext) -> list[DocumentRef]:
        documents: list[DocumentRef] = []
        while True:
            rows = page.locator("table tbody tr")
            for i in range(rows.count()):
                row = rows.nth(i)
                chave = (row.get_attribute("data-chave") or row.inner_text().split("\n")[0]).strip()
                if chave:
                    documents.append(DocumentRef(document_id=chave, title=f"NFSe_{chave}"))
            next_button = page.locator("a[rel='next'], .pagination .next a")
            if next_button.count() and next_button.first.is_enabled():
                next_button.first.click()
                page.wait_for_load_state("networkidle")
            else:
                break
        ctx.log(f"{len(documents)} documentos encontrados")
        return documents

    def download_document(self, page: Page, ctx: JobContext, doc: DocumentRef, tmp_dir: Path) -> Path:
        row = page.locator(f"tr[data-chave='{doc.document_id}']")
        trigger = (
            row.locator("a[title*='Download'], a[href*='Download']")
            if row.count()
            else page.locator(f"a[href*='{doc.document_id}']")
        )
        with page.expect_download() as download_info:
            trigger.first.click()
        download = download_info.value
        target = tmp_dir / (download.suggested_filename or f"{doc.title}.xml")
        download.save_as(target)
        return target


def _to_br_date(iso_date: str) -> str:
    year, month, day = iso_date.split("-")
    return f"{day}/{month}/{year}"
