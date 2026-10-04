"""Matriz de contratos (Onda 2A, spec §4). Seis temas."""

from dataclasses import dataclass, field


@dataclass
class MatrixItem:
    key: str
    question: str
    expected_evidence: list[str] = field(default_factory=list)


@dataclass
class Dimension:
    key: str
    title: str
    keywords: tuple[str, ...] = ()
    items: list[MatrixItem] = field(default_factory=list)


CONTRACTS_MATRIX: list[Dimension] = [
    Dimension(
        "formacao", "Formação",
        ("proposta", "aceite", "assinatura", "representação", "representacao", "anexo", "condição", "condicao"),
        [
            MatrixItem("estado", "Proposta, aceite, assinatura e representação?", ["proposta", "assinatura", "procuração", "procuracao"]),
        ],
    ),
    Dimension(
        "versoes", "Versões",
        ("minuta", "aditivo", "renovação", "renovacao", "rescisão", "rescisao", "vigência", "vigencia", "versão", "versao"),
        [
            MatrixItem("diff", "Minuta, aditivos e vigência comparáveis?", ["minuta", "aditivo", "termo"]),
        ],
    ),
    Dimension(
        "prestacao", "Prestação",
        ("obrigação", "obrigacao", "prazo", "entrega", "aceite", "sla", "medição", "medicao"),
        [
            MatrixItem("matriz", "Parte versus obrigação mapeadas?", ["contrato", "relatório", "relatorio", "termo de aceite"]),
        ],
    ),
    Dimension(
        "financeiro", "Financeiro",
        ("preço", "preco", "reajuste", "retenção", "retencao", "multa", "juros", "garantia", "pagamento"),
        [
            MatrixItem("cronograma", "Preço, reajuste, multa e garantia rastreáveis?", ["cláusula financeira", "clausula", "comprovante", "boleto"]),
        ],
    ),
    Dimension(
        "descumprimento", "Descumprimento",
        ("descumprimento", "inadimplemento", "notificação", "notificacao", "cura", "mora", "rescisão motivada"),
        [
            MatrixItem("controversia", "Evento, notificação, cura e prova?", ["notificação", "notificacao", "ata", "e-mail", "email"]),
        ],
    ),
    Dimension(
        "risco", "Risco",
        ("ambiguidade", "lacuna", "dependência", "dependencia", "foro", "arbitragem", "risco", "abusiv", "validade"),
        [
            MatrixItem("providencias", "Riscos e providências específicas?", ["parecer", "matriz de riscos"]),
        ],
    ),
]
