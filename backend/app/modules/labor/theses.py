"""Teses por polo e plano probatório (V2 §10.2/§10.3).

Objetividade bilateral (§4): cada polo recebe provas favoráveis,
adversas e lacunas. Sem premissas suficientes, a saída é hipótese
para pesquisa — nunca tese validada. Quesitos neutros, sem pressupor
conclusão médica ou técnica.
"""

from dataclasses import dataclass, field


@dataclass
class ThesisDraft:
    represented_side: str
    issue: str
    conclusion: str
    factual_premises: list[str] = field(default_factory=list)
    legal_premises: list[str] = field(default_factory=list)
    supporting_refs: list[str] = field(default_factory=list)
    adverse_refs: list[str] = field(default_factory=list)
    counterargument: str = ""
    requested_evidence: list[str] = field(default_factory=list)
    limitations: str = ""
    is_hypothesis: bool = False


def _refs_by_status(evidence: list[dict], statuses: set[str]) -> list[str]:
    return [e.get("id") for e in evidence if e.get("presence_status") in statuses]


def build_theses(
    matrix_results: list,
    evidence: list[dict],
    *,
    issues: tuple[str, ...] = ("responsabilidade", "reparacao"),
) -> list[ThesisDraft]:
    """Teses reclamante x reclamada a partir da matriz e das provas."""
    examined = set(_refs_by_status(evidence, {"examined"}))
    missing_items = [f"{r.dimension}/{r.item}" for r in matrix_results if r.status == "missing"]
    documented = {f"{r.dimension}/{r.item}": r.source_refs for r in matrix_results if r.status != "missing"}

    def premises(*keys: str) -> list[str]:
        refs: list[str] = []
        for key in keys:
            refs.extend(documented.get(key, []))
        return refs

    safety_refs = (
        premises("seguranca/treinamento", "seguranca/protecao", "seguranca/manutencao")
    )
    event_refs = premises("evento/dinamica", "evento/equipamento")
    damage_refs = premises("nexo_dano/lesao", "nexo_dano/incapacidade")
    safety_missing = [m for m in missing_items if m.startswith("seguranca/")]

    drafts: list[ThesisDraft] = []
    if "responsabilidade" in issues:
        claimant_premises = event_refs + safety_refs
        drafts.append(
            ThesisDraft(
                represented_side="claimant",
                issue="responsabilidade",
                conclusion=(
                    "Responsabilidade do empregador condicionada à prova de "
                    "risco/culpa, nexo e dano (tese a confirmar por perícia)."
                ),
                factual_premises=claimant_premises,
                legal_premises=["regra aplicável a pesquisar (verificação T07)"],
                supporting_refs=[r for r in claimant_premises if r in examined],
                adverse_refs=[e.get("id") for e in evidence if e.get("id") not in examined],
                counterargument=(
                    "Reclamada pode impugnar dinâmica, treinamento, nexo e "
                    "extensão da incapacidade."
                ),
                requested_evidence=safety_missing + ["pericia_seguranca", "pericia_medica"],
                limitations=(
                    "Fotografias e narrativa isoladas não demonstram causalidade, "
                    "data ou culpa; objetiva e culpa são fundamentos distintos."
                ),
                is_hypothesis=not claimant_premises,
            )
        )
        respondent_premises = [r for r in safety_refs + damage_refs if r in examined]
        drafts.append(
            ThesisDraft(
                represented_side="respondent",
                issue="responsabilidade",
                conclusion=(
                    "Impugnação da dinâmica, do nexo e da extensão; excludente "
                    "só se houver base fática investigável."
                ),
                factual_premises=respondent_premises,
                legal_premises=["regra aplicável a pesquisar (verificação T07)"],
                supporting_refs=respondent_premises,
                adverse_refs=event_refs + damage_refs,
                counterargument="Autor pode suprir lacunas com perícia e documentos.",
                requested_evidence=["registros_seguranca", "prontuarios_autorizados"],
                limitations=(
                    "Não sugerir culpa exclusiva do trabalhador como fato sem "
                    "documento ou narrativa que a sustente."
                ),
                is_hypothesis=True,
            )
        )
    if "reparacao" in issues:
        drafts.append(
            ThesisDraft(
                represented_side="neutral",
                issue="reparacao",
                conclusion=(
                    "Quantificação condicionada a parâmetros periciais e à "
                    "conciliação de rubricas possivelmente sobrepostas."
                ),
                factual_premises=premises("reparacao/material", "reparacao/pensao"),
                legal_premises=["parâmetros de reparação a pesquisar (verificação T07)"],
                supporting_refs=[],
                adverse_refs=[],
                counterargument="Sobreposição entre parcelas pode reduzir o total.",
                requested_evidence=["memoria_calculo", "cct_integral"],
                limitations="Parâmetro dependente de perícia não é escolhido silenciosamente.",
                is_hypothesis=True,
            )
        )
    return drafts


@dataclass
class Question:
    addressee: str  # cliente | seguranca | perito_medico | perito_seguranca
    purpose: str
    text: str
    affected_claim_ids: list[str] = field(default_factory=list)


@dataclass
class Quesito:
    text: str
    controversy: str
    affected_claim_ids: list[str] = field(default_factory=list)


def build_probation_plan(
    findings: list, *, affected_claim_ids: list[str] | None = None
) -> dict:
    """Perguntas por destinatário + quesitos neutros + documentos (§10.3)."""
    affected = list(affected_claim_ids or [])
    questions = [
        Question("cliente", "dinamica", "Quais tarefas eram realizadas e como se operava o equipamento?", affected),
        Question("cliente", "testemunhas", "Quem presenciou o evento e que registros existem?", affected),
        Question("seguranca", "protecoes", "Quais proteções e instruções existiam na data e como eram documentadas?", affected),
        Question("perito_medico", "repercussao", "Qual a repercussão funcional, sua duração e relação com as atividades habituais?", affected),
        Question("perito_seguranca", "condicoes", "Quais condições técnicas são verificáveis e quais dependem de registros históricos?", affected),
    ]
    quesitos = [
        Quesito(
            "Quais lesões foram constatadas e qual a limitação funcional atual?",
            "nexo_dano/incapacidade", affected,
        ),
        Quesito(
            "As condições de segurança apuradas são compatíveis com a norma vigente à época?",
            "seguranca/norma_temporal", affected,
        ),
        Quesito(
            "Há elementos técnicos que afastem o nexo entre evento e lesão?",
            "responsabilidade/objetiva", affected,
        ),
    ]
    documents = [
        "CAT, se existente",
        "comunicações e decisões previdenciárias",
        "prontuários e laudos autorizados",
        "fichas de treinamento e EPI",
        "registros de manutenção e salariais",
        "CCT integral com vigência e cláusula",
    ]
    return {"questions": questions, "quesitos": quesitos, "documents": documents}
