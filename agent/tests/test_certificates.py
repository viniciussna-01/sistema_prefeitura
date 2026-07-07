from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from sistema_agent.certificates import extract_cnpj_cpf_from_subject, parse_certificate


def test_extract_cnpj_from_icp_brasil_cn():
    assert extract_cnpj_cpf_from_subject("EMPRESA TESTE LTDA:12345678000199") == "12345678000199"
    assert extract_cnpj_cpf_from_subject("JOAO DA SILVA:12345678901") == "12345678901"
    assert extract_cnpj_cpf_from_subject("SEM DOCUMENTO") is None
    assert extract_cnpj_cpf_from_subject("NOME:ABC") is None


def _self_signed_der(common_name: str) -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.DER)


def test_parse_certificate_metadata_only():
    der = _self_signed_der("EMPRESA TESTE LTDA:12345678000199")
    info = parse_certificate(der)
    assert info is not None
    assert info.cnpj_cpf == "12345678000199"
    assert len(info.thumbprint) == 40  # SHA-1 hex
    assert info.not_after > info.not_before
    report = info.to_report()
    # O relatório contém apenas metadados — nenhum material de chave
    assert set(report) == {
        "thumbprint", "subject", "issuer", "cnpj_cpf",
        "certificate_type", "not_before", "not_after",
    }


def test_parse_invalid_bytes_returns_none():
    assert parse_certificate(b"nao-e-um-certificado") is None
