"""Loop principal do agente: heartbeat, sincronização de certificados,
busca de trabalhos e execução das automações com Playwright."""

import logging
import tempfile
import threading
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

from sistema_agent.api_client import ApiClient
from sistema_agent.automation.base import JobContext
from sistema_agent.automation.registry import get_adapter
from sistema_agent.browser import auto_select_certificate, launch_browser
from sistema_agent.certificates import list_windows_certificates
from sistema_agent.config import AgentConfig
from sistema_agent.downloads import DownloadOrganizer

logger = logging.getLogger(__name__)


class AgentRunner:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.api = ApiClient(config)
        self._stop = threading.Event()
        self.current_job: str | None = None

    def stop(self) -> None:
        self._stop.set()

    def run_forever(self) -> None:
        last_heartbeat = 0.0
        last_cert_sync = 0.0
        while not self._stop.is_set():
            now = time.monotonic()
            try:
                if now - last_heartbeat >= self.config.heartbeat_interval_seconds:
                    self.api.heartbeat()
                    last_heartbeat = now
                if now - last_cert_sync >= 300:
                    self.sync_certificates()
                    last_cert_sync = now

                for job in self.api.poll_jobs():
                    self.execute_job(job)
            except Exception:
                logger.exception("Erro no loop do agente; tentando novamente")
            self._stop.wait(self.config.poll_interval_seconds)

    def sync_certificates(self) -> None:
        certificates = list_windows_certificates()
        self.api.report_certificates([c.to_report() for c in certificates])
        logger.info("%d certificados sincronizados", len(certificates))

    def execute_job(self, job: dict) -> None:
        execution_id = job["execution_id"]
        self.current_job = execution_id
        cancelled = {"flag": job.get("cancel_requested", False)}

        def log(message: str) -> None:
            logger.info("[%s] %s", execution_id, message)
            result = self.api.update_job(execution_id, logs=[{"level": "info", "message": message}])
            cancelled["flag"] = cancelled["flag"] or result.get("cancel_requested", False)

        try:
            adapter = get_adapter(job["portal"])
            self.api.update_job(execution_id, status="running")
            log(f"Iniciando automação do portal {job['portal']} para {job['company_name']}")

            organizer = DownloadOrganizer(self.config.downloads_dir)
            ctx = JobContext(
                company_name=job["company_name"],
                company_cnpj=job["company_cnpj"],
                filters=job["filters"],
                log=log,
                is_cancelled=lambda: cancelled["flag"],
            )

            with sync_playwright() as playwright:
                with auto_select_certificate(f"{adapter.certificate_url_pattern}/*"):
                    browser = launch_browser(playwright, headless=self.config.headless)
                    context = browser.new_context(accept_downloads=True)
                    page = context.new_page()
                    try:
                        adapter.authenticate(page, ctx)
                        adapter.apply_filters(page, ctx)
                        documents = adapter.list_documents(page, ctx)

                        with tempfile.TemporaryDirectory() as tmp:
                            tmp_dir = Path(tmp)
                            for index, doc in enumerate(documents, start=1):
                                if ctx.is_cancelled():
                                    log("Cancelamento solicitado — interrompendo downloads")
                                    self.api.update_job(execution_id, status="cancelled")
                                    return
                                downloaded = adapter.download_document(page, ctx, doc, tmp_dir)
                                stored = organizer.store(
                                    job["company_name"],
                                    downloaded,
                                    downloaded.name,
                                    document_id=doc.document_id,
                                )
                                self.api.update_job(
                                    execution_id,
                                    downloads=[stored.__dict__],
                                    logs=[{
                                        "level": "info",
                                        "message": f"Download {index}/{len(documents)}: {stored.file_name}",
                                    }],
                                )
                        self.api.update_job(execution_id, status="success")
                        log("Execução concluída com sucesso")
                    except Exception as error:
                        screenshot = None
                        try:
                            screenshot = page.screenshot(full_page=True)
                        except Exception:
                            pass
                        self.api.log(
                            execution_id,
                            f"Falha na automação: {error}",
                            level="error",
                            screenshot=screenshot,
                        )
                        self.api.update_job(
                            execution_id,
                            status="failed",
                            error_message=f"{error}\n{traceback.format_exc(limit=5)}",
                        )
                    finally:
                        context.close()
                        browser.close()
        except Exception as error:
            logger.exception("Erro fatal na execução %s", execution_id)
            try:
                self.api.update_job(execution_id, status="failed", error_message=str(error))
            except Exception:
                pass
        finally:
            self.current_job = None
