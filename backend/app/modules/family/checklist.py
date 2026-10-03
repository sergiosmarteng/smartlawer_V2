"""Matriz de família e sucessões (Onda 1A, spec §5).

Seis dimensões; cada item declara a prova esperada. Alegação não é
prova: referência a alegação nunca marca o item como ``documented``.
"""

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


FAMILY_MATRIX: list[Dimension] = [
    Dimension(
        "pessoas_vinculos", "Pessoas e vínculos",
        ("parentesco", "filiação", "filiacao", "idade", "guarda", "filho", "dependente"),
        [
            MatrixItem("parentesco", "Parentesco e filiação comprovados?", ["certidão", "documento"]),
            MatrixItem("capacidade", "Capacidade e representação?", ["documento", "curatela"]),
        ],
    ),
    Dimension(
        "guarda_convivencia", "Guarda e convivência",
        ("guarda", "convivência", "convivencia", "visita", "lar", "residência", "residencia"),
        [
            MatrixItem("situacao", "Situação atual da criança?", ["estudo_social", "escola", "testemunha"]),
            MatrixItem("risco", "Alegação de risco com suporte?", ["estudo_social", "boletim", "perícia", "pericia"]),
        ],
    ),
    Dimension(
        "alimentos", "Alimentos",
        ("alimentos", "pensão", "pensao", "renda", "despesa", "necessidade", "possibilidade"),
        [
            MatrixItem("necessidade", "Necessidade comprovada?", ["despesa", "escola", "saúde", "saude"]),
            MatrixItem("capacidade", "Capacidade do alimentante documentada?", ["contracheque", "extrato", "declaração", "declaracao"]),
        ],
    ),
    Dimension(
        "divorcio_patrimonio", "Divórcio e patrimônio",
        ("divórcio", "divorcio", "regime de bens", "patrimônio", "patrimonio", "partilha", "imóvel", "imovel"),
        [
            MatrixItem("regime", "Regime de bens e datas?", ["certidão de casamento", "certidao", "pacto"]),
            MatrixItem("bens", "Bens e dívidas inventariados?", ["matrícula", "matricula", "avaliação", "avaliacao"]),
        ],
    ),
    Dimension(
        "sucessoes", "Sucessões",
        ("óbito", "obito", "herdeiro", "testamento", "inventário", "inventario", "partilha", "espólio", "espolio"),
        [
            MatrixItem("interessados", "Óbito, herdeiros e testamento?", ["certidão de óbito", "certidao", "testamento"]),
            MatrixItem("acervo", "Bens, dívidas e doações?", ["matrícula", "matricula", "extrato"]),
        ],
    ),
    Dimension(
        "medidas_urgentes", "Medidas urgentes",
        ("tutela", "urgente", "proteção", "protecao", "risco imediato", "liminar"),
        [
            MatrixItem("urgencia", "Requisitos da tutela com prova?", ["documento", "foto", "boletim"]),
        ],
    ),
]
