"""Matriz empresarial e societária (Onda 2A, spec §3). Sete temas."""

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


CORPORATE_MATRIX: list[Dimension] = [
    Dimension(
        "estrutura", "Estrutura",
        ("sociedade", "sócio", "socios", "sócios", "acionista", "administrador", "controlada", "filial", "participação", "participacao"),
        [
            MatrixItem("grafo", "Sociedades, sócios, poderes e filiais?", ["contrato social", "estatuto", "cnpj"]),
        ],
    ),
    Dimension(
        "atos", "Atos",
        ("ata", "assembleia", "alteração contratual", "alteracao", "registro", "deliberação", "deliberacao", "procuração", "procuracao"),
        [
            MatrixItem("cronologia", "Atos, registros e deliberações com validade?", ["ata", "junta comercial", "publicação", "publicacao"]),
        ],
    ),
    Dimension(
        "governanca", "Governança",
        ("quórum", "quorum", "convocação", "convocacao", "conflito de interesse", "dever", "representação", "representacao"),
        [
            MatrixItem("checklist", "Quórum, convocação e representação?", ["edital de convocação", "edital", "estatuto", "lista de presença", "lista"]),
        ],
    ),
    Dimension(
        "capital_quotas", "Capital e quotas",
        ("capital", "quota", "subscrição", "subscricao", "integralização", "integralizacao", "cessão", "cessao", "preferência", "preferencia"),
        [
            MatrixItem("quadro", "Subscrição, integralização e cessões?", ["contrato social", "livro", "recibo"]),
        ],
    ),
    Dimension(
        "obrigacoes", "Obrigações",
        ("garantia", "dívida", "divida", "devedor", "distribuição", "distribuicao", "prestação de contas", "prestacao", "responsabilidade", "administrador", "sócio"),
        [
            MatrixItem("matriz", "Obrigação versus parte mapeadas?", ["contrato", "balanço", "balanco", "extrato"]),
        ],
    ),
    Dimension(
        "crise", "Crise",
        ("inadimplência", "inadimplencia", "renegociação", "renegociacao", "recuperação", "recuperacao", "falência", "falencia", "credor"),
        [
            MatrixItem("alertas", "Pedido, deferimento e concessão distintos?", ["petição", "peticao", "decisão", "decisao", "edital"]),
        ],
    ),
    Dimension(
        "prova", "Prova",
        ("livro", "demonstra", "e-mail", "email", "documento", "testemunha"),
        [
            MatrixItem("exame", "Livros, atas, demonstrativos e registros?", ["livro", "ata assinada", "demonstrativo", "registro"]),
        ],
    ),
]
