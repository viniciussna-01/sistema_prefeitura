"use client";

import { useEffect, useState } from "react";

import { Badge, EmptyState, Spinner, Table } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { Certificate } from "@/lib/types";

function expiryTone(notAfter: string | null): "green" | "amber" | "red" {
  if (!notAfter) return "green";
  const days = (new Date(notAfter).getTime() - Date.now()) / 86400000;
  if (days < 0) return "red";
  if (days < 30) return "amber";
  return "green";
}

export default function CertificatesPage() {
  const [certificates, setCertificates] = useState<Certificate[] | null>(null);

  useEffect(() => {
    api<Certificate[]>("/certificates").then(setCertificates);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Certificados digitais</h1>
        <p className="text-sm text-ink-muted">
          Detectados automaticamente pelos agentes desktop. Somente metadados são enviados — a
          chave privada nunca sai da máquina do cliente.
        </p>
      </div>

      {!certificates ? (
        <Spinner />
      ) : certificates.length === 0 ? (
        <EmptyState message="Nenhum certificado detectado. Instale e matricule um agente desktop em uma máquina com certificados." />
      ) : (
        <Table headers={["Titular", "CNPJ/CPF", "Tipo", "Emissor", "Validade"]}>
          {certificates.map((certificate) => (
            <tr key={certificate.id} className="hover:bg-surface">
              <td className="max-w-xs truncate px-4 py-3 font-medium" title={certificate.subject}>
                {certificate.subject}
              </td>
              <td className="px-4 py-3 text-ink-muted">{certificate.cnpj_cpf ?? "—"}</td>
              <td className="px-4 py-3">
                <Badge tone="blue">{certificate.certificate_type}</Badge>
              </td>
              <td className="max-w-xs truncate px-4 py-3 text-ink-muted" title={certificate.issuer}>
                {certificate.issuer}
              </td>
              <td className="px-4 py-3">
                <Badge tone={expiryTone(certificate.not_after)}>
                  {formatDate(certificate.not_after)}
                </Badge>
              </td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}
