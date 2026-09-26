"""Achados que distinguem análise útil: divergências com fonte, impacto e ação (V2 §18.5).

Regras genéricas sobre o artefato — nenhum nome, valor ou número do
caso de validação codificado na lógica de produção.
"""

from dataclasses import dataclass, field


@dataclass
class Finding:
    code: str
    affected_claim_ids: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
    description: str = ""
    impact: str = ""
    missing_info: str = ""
    suggested_action: str = ""


def _claim_by_id(claims: list[dict], claim_id: str) -> dict | None:
    for claim in claims:
        if claim.get("id") == claim_id:
            return claim
    return None


def detect_term_divergence(claims: list[dict]) -> list[Finding]:
    """Termo inicial/duração do pensionamento divergentes entre corpo e pedido."""
    findings: list[Finding] = []
    pensions = [c for c in claims if (c.get("category") or "") == "pensao"]
    starts = {c.get("id"): c.get("period") for c in pensions if c.get("period")}
    if len(set(starts.values())) > 1:
        findings.append(
            Finding(
                code="PENSION_TERM_DIVERGENCE",
                affected_claim_ids=list(starts),
                description=(
                    "Termo inicial/duração do pensionamento diverge entre "
                    "ocorrências (ex.: evento x ajuizamento; vitalícia x limite etário)."
                ),
                impact="Altera base de cálculo e pedidos dependentes.",
                missing_info="Critério adotado para termo inicial e termo final.",
                suggested_action="Conciliar ocorrências e confirmar com o cliente; não decidir automaticamente.",
            )
        )
    for claim in pensions:
        relief = (claim.get("requested_relief") or "").casefold()
        if "vital" in relief and claim.get("period"):
            findings.append(
                Finding(
                    code="PENSION_VITALICIA_VS_CAP",
                    affected_claim_ids=[claim.get("id")],
                    description="Descrição 'vitalícia' convive com limite etário/temporal.",
                    impact="Conceitos distintos de duração; cálculo muda.",
                    missing_info="Natureza pretendida: vitalícia ou temporária até idade-limite.",
                    suggested_action="Exigir conciliação conceitual antes de quantificar cenários.",
                )
            )
    return findings


def detect_period_arithmetic(claims: list[dict], facts: list[dict]) -> list[Finding]:
    """Durações declaradas x aritmética das datas (ex.: 65-33=32 ≠ 31)."""
    findings: list[Finding] = []
    for fact in facts:
        declared = fact.get("declared_years")
        start_age = fact.get("start_age")
        end_age = fact.get("end_age")
        if declared is not None and start_age is not None and end_age is not None:
            try:
                computed = int(end_age) - int(start_age)
                if int(declared) != computed:
                    findings.append(
                        Finding(
                            code="PERIOD_ARITHMETIC_MISMATCH",
                            description=(
                                f"Duração declarada ({declared} anos) diverge da "
                                f"aritmética das idades ({end_age}-{start_age}={computed})."
                            ),
                            impact="Base temporal do pensionamento incerta.",
                            missing_info="Data de nascimento e período adotado.",
                            suggested_action="Esclarecer base temporal; não substituir sem validação.",
                        )
                    )
            except (TypeError, ValueError):
                continue
    return findings


def detect_overlaps(claims: list[dict]) -> list[Finding]:
    """Possível sobreposição entre rubricas (hipótese a revisar, §10.2)."""
    findings: list[Finding] = []
    for claim in claims:
        for rel in claim.get("related_claims", []) or []:
            if rel.get("relation") == "overlaps":
                other = _claim_by_id(claims, rel.get("claim_id"))
                findings.append(
                    Finding(
                        code="POSSIBLE_OVERLAP",
                        affected_claim_ids=[claim.get("id"), rel.get("claim_id")],
                        description=(
                            f"Possível sobreposição entre '{claim.get('title')}' e "
                            f"'{(other or {}).get('title')}'."
                        ),
                        impact="Risco de bis in idem se fatos geradores coincidirem.",
                        missing_info="Fatos geradores e finalidades de cada parcela.",
                        suggested_action=(
                            "Examinar fatos geradores; apontar sobreposição, "
                            "não declarar bis in idem sem exame."
                        ),
                    )
                )
    return findings


def detect_missing_collective_instrument(
    claims: list[dict], evidence: list[dict]
) -> list[Finding]:
    """CCT citada sem instrumento integral no conjunto (§18.4)."""
    examined_docs = {
        (e.get("kind"), e.get("presence_status")) for e in evidence
    }
    cct_examined = any(
        kind == "cct" and status == "examined" for kind, status in examined_docs
    )
    findings: list[Finding] = []
    if cct_examined:
        return findings
    for claim in claims:
        text = f"{claim.get('title', '')} {claim.get('requested_relief', '')}".casefold()
        if "cct" in text or "coletiv" in text or "normativ" in text:
            findings.append(
                Finding(
                    code="MISSING_CCT",
                    affected_claim_ids=[claim.get("id")],
                    description="Pedido fundado em instrumento coletivo não localizado no conjunto.",
                    impact="Requisito (vigência, cláusula, fato gerador) sem comprovação.",
                    missing_info="CCT integral, vigência, categoria, cláusula aplicável.",
                    suggested_action="Solicitar CCT e documento do fato gerador.",
                )
            )
    return findings


def detect_photo_without_medical_report(evidence: list[dict]) -> list[Finding]:
    """Fotografia não certifica diagnóstico, data ou culpa (§18.4)."""
    has_photo = any(e.get("kind") == "photo" for e in evidence)
    has_report = any(
        e.get("kind") in ("laudo", "pericia_medica", "prontuario")
        and e.get("presence_status") == "examined"
        for e in evidence
    )
    if has_photo and not has_report:
        return [
            Finding(
                code="PHOTO_NOT_DIAGNOSIS",
                description="Imagens examinadas sem laudo/perícia correspondente no conjunto.",
                impact="Grau de incapacidade, data e causalidade seguem controversos.",
                missing_info="Documento clínico e perícia.",
                suggested_action="Requerer perícia; não inferir incapacidade por fotografia.",
            )
        ]
    return []


def run_all_detectors(artifact: dict) -> list[Finding]:
    """Todos os detectores sobre o artefato (claims/facts/evidence como dicts)."""
    claims = artifact.get("claims", [])
    facts = artifact.get("facts", [])
    evidence = artifact.get("evidence", [])
    findings: list[Finding] = []
    findings.extend(detect_term_divergence(claims))
    findings.extend(detect_period_arithmetic(claims, facts))
    findings.extend(detect_overlaps(claims))
    findings.extend(detect_missing_collective_instrument(claims, evidence))
    findings.extend(detect_photo_without_medical_report(evidence))
    return findings
