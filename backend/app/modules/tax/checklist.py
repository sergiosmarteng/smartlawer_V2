"""Matriz tributária (Onda 2B, spec §5). Sete temas."""

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


TAX_MATRIX: list[Dimension] = [
    Dimension(
        "competencia", "Competência",
        ("ente", "tributo", "contribuinte", "responsável", "responsavel", "icm", "icms", "iss", "iptu", "itbi", "competência", "competencia"),
        [
            MatrixItem("jurisdicao", "Ente, tributo, período e regime?", ["auto de infração", "auto", "lei do ente", "cnpj"]),
        ],
    ),
    Dimension(
        "fato_gerador", "Fato gerador",
        ("fato gerador", "operação", "operacao", "base de cálculo", "base de calculo", "classificação", "classificacao"),
        [
            MatrixItem("premissas", "Operação, data, local e base documentais?", ["nota fiscal", "contrato", "escrituração", "escrituracao"]),
        ],
    ),
    Dimension(
        "lancamento", "Lançamento",
        ("lançamento", "lancamento", "auto", "declaração", "declaracao", "notificação", "notificacao", "ciência", "ciencia", "impugnação", "impugnacao"),
        [
            MatrixItem("linha", "Auto, declaração, ciência e impugnação?", ["auto", "aviso", "protocolo"]),
        ],
    ),
    Dimension(
        "credito", "Crédito",
        ("crédito", "credito", "principal", "multa", "juros", "correção", "correcao", "pagamento", "compensação", "compensacao"),
        [
            MatrixItem("quadro", "Principal, multa, juros, pagamentos por competência?", ["demonstrativo", "extrato", "guia"]),
        ],
    ),
    Dimension(
        "beneficio_regime", "Benefício/regime",
        ("isenção", "isencao", "imunidade", "alíquota", "aliquota", "benefício", "beneficio", "enquadramento", "opção", "opcao"),
        [
            MatrixItem("condicoes", "Opção, enquadramento e condições verificados?", ["opção", "opcao", "certidão", "certidao", "lei"]),
        ],
    ),
    Dimension(
        "tempo", "Tempo",
        ("decadência", "decadencia", "prescrição", "prescricao", "suspensão", "suspensao", "interrupção", "interrupcao", "marco"),
        [
            MatrixItem("analise", "Marcos e causas suspensivas sustentados?", ["intimação", "intimacao", "protocolo", "decisão", "decisao"]),
        ],
    ),
    Dimension(
        "reforma", "Reforma",
        ("reforma tributária", "reforma tributaria", "transição", "transicao", "vigência", "vigencia", "produção de efeitos", "producao"),
        [
            MatrixItem("tabela", "Tabela de vigência e efeitos por tributo/período?", ["lei", "tabela oficial", "ato"]),
        ],
    ),
]
