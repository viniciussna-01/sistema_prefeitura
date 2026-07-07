"""Adaptador da NFS-e da Prefeitura de São Paulo (nfe.prefeitura.sp.gov.br).

ATENÇÃO: seletores sujeitos a mudanças no portal — mantidos isolados
neste adaptador. A Prefeitura de SP também oferece web service oficial de
consulta (com certificado); se for habilitado para o contribuinte,
prefira criar um adaptador de API em vez deste, mantendo o mesmo contrato.
"""

from pathlib import Path

from playwright.sync_api import Page

from sistema_agent.automation.base import DocumentRef, JobContext, PortalAdapter

BASE_URL = "https://nfe.prefeitura.sp.gov.br"


class NfseSaoPauloAdapter(PortalAdapter):
    certificate_url_pattern = "https://nfe.prefeitura.sp.gov.br"

    def authenticate(self, page: Page, ctx: JobContext) -> None:
        ctx.log("Abrindo o portal NFS-e da Prefeitura de São Paulo")
        page.goto(f"{BASE_URL}/login.aspx", wait_until="domcontentloaded")
        page.get_by_role("link", name="Certificação Digital").or_(
            page.locator("a[href*='certificado']")
        ).first.click()
        page.wait_for_load_state("networkidle")

        if "login" in page.url.lower():
            raise RuntimeError("Autenticação com certificado digital falhou no portal de SP")
        ctx.log("Autenticado com certificado digital")

        # Portais multi-CNPJ: seleciona o contribuinte correspondente à empresa
        cnpj_digits = "".join(c for c in ctx.company_cnpj if c.isdigit())
        selector = page.locator(f"a:has-text('{cnpj_digits}'), option:has-text('{cnpj_digits}')")
        if selector.count():
            selector.first.click()
            page.wait_for_load_state("networkidle")

    def apply_filters(self, page: Page, ctx: JobContext) -> None:
        start = ctx.filters["start_date"]
        end = ctx.filters["end_date"]
        ctx.log(f"Aplicando filtro de período: {start} a {end}")

        page.goto(f"{BASE_URL}/contribuinte/notasrecebidas.aspx", wait_until="domcontentloaded")
        page.fill("input[id*='dataInicial'], input[name*='dataInicial']", _to_br_date(start))
        page.fill("input[id*='dataFinal'], input[name*='dataFinal']", _to_br_date(end))
        page.get_by_role("button", name="Pesquisar").or_(
            page.locator("input[type='submit'][value*='Pesquisar']")
        ).first.click()
        page.wait_for_load_state("networkidle")

    def list_documents(self, page: Page, ctx: JobContext) -> list[DocumentRef]:
        documents: list[DocumentRef] = []
        page_number = 1
        while True:
            rows = page.locator("table[id*='grd'] tbody tr, table.grid tbody tr")
            for i in range(rows.count()):
                text = rows.nth(i).inner_text().strip()
                if not text:
                    continue
                numero = text.split("\n")[0].split("\t")[0].strip()
                if numero and numero.lower() not in ("número", "numero"):
                    documents.append(
                        DocumentRef(document_id=f"p{page_number}r{i}_{numero}", title=f"NFSe_SP_{numero}")
                    )
            next_button = page.locator("a[id*='Proxima'], a:has-text('Próxima')")
            if next_button.count() and next_button.first.is_visible():
                next_button.first.click()
                page.wait_for_load_state("networkidle")
                page_number += 1
            else:
                break
        ctx.log(f"{len(documents)} documentos encontrados")
        return documents

    def download_document(self, page: Page, ctx: JobContext, doc: DocumentRef, tmp_dir: Path) -> Path:
        numero = doc.title.rsplit("_", 1)[-1]
        trigger = page.locator(
            f"a[href*='exporta'][href*='{numero}'], "
            f"tr:has-text('{numero}') a[title*='Exportar'], "
            f"tr:has-text('{numero}') a[href*='xml']"
        )
        with page.expect_download() as download_info:
            trigger.first.click()
        download = download_info.value
        target = tmp_dir / (download.suggested_filename or f"{doc.title}.xlsx")
        download.save_as(target)
        return target


def _to_br_date(iso_date: str) -> str:
    year, month, day = iso_date.split("-")
    return f"{day}/{month}/{year}"
