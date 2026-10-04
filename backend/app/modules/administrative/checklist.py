"""Matriz administrativa (Onda 2B, spec §6). Seis temas."""

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


ADMINISTRATIVE_MATRIX: list[Dimension] = [
    Dimension(
        "ente_agente", "Ente e agente",
        ("ente", "órgão", "orgao", "autoridade", "delegação", "delegacao", "município", "municipio", "estado", "união", "uniao"),
        [
            MatrixItem("mapa", "Esfera, órgão, autoridade e interessado?", ["lei", "decreto", "portaria", "ato"]),
        ],
    ),
    Dimension(
        "ato", "Ato",
        ("ato administrativo", "motivação", "motivacao", "publicação", "publicacao", "ciência", "ciencia", "forma", "objeto"),
        [
            MatrixItem("requisitos", "Motivação, forma, objeto e ciência?", ["diário oficial", "diario", "publicação", "publicacao"]),
        ],
    ),
    Dimension(
        "processo", "Processo",
        ("processo administrativo", "requerimento", "defesa", "instrução", "instrucao", "recurso administrativo"),
        [
            MatrixItem("cronologia", "Requerimento, defesa, instrução e recurso?", ["protocolo", "parecer", "decisão", "decisao"]),
        ],
    ),
    Dimension(
        "licitacao", "Licitação",
        ("licitação", "licitacao", "edital", "pregão", "pregao", "habilitação", "habilitacao", "proposta", "julgamento", "certame"),
        [
            MatrixItem("comparacao", "Edital, critérios, propostas e julgamento?", ["edital", "ata", "proposta", "certidão", "certidao"]),
        ],
    ),
    Dimension(
        "contrato_publico", "Contrato público",
        ("contrato administrativo", "medição", "medicao", "aditivo", "sanção", "sancao", "execução", "execucao", "equilíbrio", "equilibrio"),
        [
            MatrixItem("obrigacoes", "Matriz de riscos, medição, aditivos e sanções?", ["contrato", "medição", "medicao", "termo"]),
        ],
    ),
    Dimension(
        "responsabilizacao", "Responsabilização",
        ("imputação", "imputacao", "sanção", "sancao", "multa administrativa", "responsabilidade", "defesa", "culpa", "dolo", "denúncia", "denuncia", "notícia", "noticia", "relatório", "relatorio", "irregularidade"),
        [
            MatrixItem("bilateral", "Imputação, prova e defesa condicionadas?", ["processo", "notificação", "notificacao", "laudo"]),
        ],
    ),
]
