"""Matriz cível e processo civil (Onda 1A, spec §4). Sete temas."""

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


CIVIL_PROCEDURE_MATRIX: list[Dimension] = [
    Dimension(
        "relacao_material", "Relação material",
        ("obrigação", "obrigacao", "inadimplemento", "dano", "nexo", "contrato", "título", "titulo"),
        [
            MatrixItem("premissas", "Obrigação, inadimplemento, dano e nexo mapeados?", ["contrato", "pagamento", "notificação", "notificacao"]),
        ],
    ),
    Dimension(
        "rito_competencia", "Rito e competência",
        ("foro", "competência", "competencia", "rito", "juizado", "valor da causa", "cláusula de eleição", "clausula"),
        [
            MatrixItem("competencia", "Natureza, partes e rito verificados?", ["petição inicial", "peticao", "contrato"]),
        ],
    ),
    Dimension(
        "pecas_atos", "Peças e atos",
        ("inicial", "contestação", "contestacao", "réplica", "replica", "recurso", "decisão", "decisao", "cumprimento"),
        [
            MatrixItem("fase", "Fase e ônus por ato?", ["peça", "peca", "decisão", "decisao"]),
        ],
    ),
    Dimension(
        "tutela_provisoria", "Tutela provisória",
        ("tutela", "urgência", "urgencia", "perigo", "reversibilidade", "contracautela", "liminar"),
        [
            MatrixItem("requisitos", "Urgência, perigo e reversibilidade com prova?", ["documento", "foto", "laudo"]),
        ],
    ),
    Dimension(
        "prova", "Prova",
        ("ônus", "onus", "perícia", "pericia", "testemunha", "documento", "autenticidade"),
        [
            MatrixItem("distribuicao", "Distribuição do ônus e meios mapeaados?", ["documento", "testemunha", "perícia", "pericia"]),
        ],
    ),
    Dimension(
        "tempo", "Tempo",
        ("prescrição", "prescricao", "decadência", "decadencia", "intimação", "intimacao", "preclusão", "preclusao", "coisa julgada"),
        [
            MatrixItem("marcos", "Marcos temporais sustentados?", ["intimação", "intimacao", "protocolo", "publicação", "publicacao"]),
        ],
    ),
    Dimension(
        "remedios", "Remédios",
        ("obrigação de fazer", "obrigacao", "cobrança", "cobranca", "indenização", "indenizacao", "rescisão", "rescisao", "execução", "execucao"),
        [
            MatrixItem("consequencias", "Consequências e relações entre pedidos?", ["pedido", "contrato", "sentença", "sentenca"]),
        ],
    ),
]
