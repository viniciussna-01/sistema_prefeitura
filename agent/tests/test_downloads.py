from datetime import datetime
from pathlib import Path

from sistema_agent.downloads import DownloadOrganizer, sanitize_name


def _make_source(tmp_path: Path, name: str, content: bytes = b"conteudo") -> Path:
    source = tmp_path / "staging" / name
    source.parent.mkdir(exist_ok=True)
    source.write_bytes(content)
    return source


def test_sanitize_name():
    assert sanitize_name("Empresa Ação & Cia") == "Empresa_Acao_Cia"
    assert sanitize_name("///") == "arquivo"


def test_store_keeps_files_separated_by_company(tmp_path: Path):
    organizer = DownloadOrganizer(tmp_path / "downloads")

    for company in ("Empresa A", "Empresa B"):
        source = _make_source(tmp_path, "Documento_001.xlsx")
        stored = organizer.store(company, source, "Documento_001.xlsx")
        assert Path(stored.local_path).exists()

    assert (tmp_path / "downloads" / "Empresa_A" / "Documento_001.xlsx").exists()
    assert (tmp_path / "downloads" / "Empresa_B" / "Documento_001.xlsx").exists()


def test_collision_renames_with_company_date_time_id(tmp_path: Path):
    organizer = DownloadOrganizer(tmp_path / "downloads")
    when = datetime(2026, 7, 6, 10, 15, 0)

    first = organizer.store("Empresa A", _make_source(tmp_path, "doc.xlsx"), "doc.xlsx")
    second = organizer.store(
        "Empresa A", _make_source(tmp_path, "doc.xlsx", b"outro"), "doc.xlsx",
        document_id="123", now=when,
    )

    assert Path(first.local_path).name == "doc.xlsx"
    assert Path(second.local_path).name == "Empresa_A_20260706_101500_123.xlsx"
    # Ambos os arquivos coexistem — nunca são consolidados
    assert Path(first.local_path).exists() and Path(second.local_path).exists()
    assert first.sha256 != second.sha256


def test_repeated_collisions_get_counter(tmp_path: Path):
    organizer = DownloadOrganizer(tmp_path / "downloads")
    when = datetime(2026, 7, 6, 10, 15, 0)

    organizer.store("Empresa A", _make_source(tmp_path, "doc.xlsx"), "doc.xlsx")
    a = organizer.store("Empresa A", _make_source(tmp_path, "doc.xlsx"), "doc.xlsx", now=when)
    b = organizer.store("Empresa A", _make_source(tmp_path, "doc.xlsx"), "doc.xlsx", now=when)

    assert Path(a.local_path).name != Path(b.local_path).name
