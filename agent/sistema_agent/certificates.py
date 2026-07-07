"""Detecção de certificados digitais instalados no Windows.

Enumera o repositório pessoal ("MY") do usuário via CryptoAPI e extrai
apenas METADADOS (titular, emissor, validade, CNPJ/CPF). A chave privada
permanece protegida pelo sistema operacional / token criptográfico e
nunca é exportada — a autenticação TLS acontece dentro do navegador,
que usa o repositório do Windows nativamente.
"""

import platform
from dataclasses import dataclass
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes

# OIDs ICP-Brasil (otherName no SAN)
OID_ICP_PF_DADOS = "2.16.76.1.3.1"   # dados do titular PF (contém CPF)
OID_ICP_PJ_CNPJ = "2.16.76.1.3.3"    # CNPJ do titular PJ


@dataclass
class CertificateInfo:
    thumbprint: str
    subject: str
    issuer: str
    cnpj_cpf: str | None
    certificate_type: str  # "A1" | "A3"
    not_before: datetime
    not_after: datetime

    def to_report(self) -> dict:
        return {
            "thumbprint": self.thumbprint,
            "subject": self.subject,
            "issuer": self.issuer,
            "cnpj_cpf": self.cnpj_cpf,
            "certificate_type": self.certificate_type,
            "not_before": self.not_before.isoformat(),
            "not_after": self.not_after.isoformat(),
        }


def extract_cnpj_cpf_from_subject(subject_cn: str) -> str | None:
    """Certificados ICP-Brasil usam CN no formato 'NOME:CNPJ' ou 'NOME:CPF'."""
    if ":" not in subject_cn:
        return None
    candidate = subject_cn.rsplit(":", 1)[-1].strip()
    if candidate.isdigit() and len(candidate) in (11, 14):
        return candidate
    return None


def parse_certificate(der_bytes: bytes) -> CertificateInfo | None:
    try:
        cert = x509.load_der_x509_certificate(der_bytes)
    except ValueError:
        return None

    thumbprint = cert.fingerprint(hashes.SHA1()).hex().upper()
    subject = cert.subject.rfc4514_string()
    issuer = cert.issuer.rfc4514_string()

    cn_attrs = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    common_name = cn_attrs[0].value if cn_attrs else ""
    cnpj_cpf = extract_cnpj_cpf_from_subject(str(common_name))

    return CertificateInfo(
        thumbprint=thumbprint,
        subject=subject,
        issuer=issuer,
        cnpj_cpf=cnpj_cpf,
        # A distinção A1/A3 real depende do provedor criptográfico (CSP/KSP);
        # certificados em token/smartcard aparecem como não exportáveis.
        # Heurística conservadora: reportar A1 e permitir ajuste no dashboard.
        certificate_type="A1",
        not_before=cert.not_valid_before_utc,
        not_after=cert.not_valid_after_utc,
    )


def list_windows_certificates() -> list[CertificateInfo]:
    """Lista certificados do repositório pessoal do usuário no Windows."""
    if platform.system() != "Windows":
        return []

    import wincertstore

    results: list[CertificateInfo] = []
    with wincertstore.CertSystemStore("MY") as store:
        for pem_cert in store.itercerts(usage=None):
            der = pem_cert.get_encoded()
            info = parse_certificate(der)
            if info is not None:
                results.append(info)
    return results
