"""Matriz previdenciária (Onda 1B, spec §8). Seis temas."""

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


SOCIAL_SECURITY_MATRIX: list[Dimension] = [
    Dimension(
        "regime", "Regime",
        ("rgps", "rpps", "inss", "regime", "benefício", "beneficio", "espécie", "especie"),
        [
            MatrixItem("identificacao", "Regime, órgão e benefício identificados?", ["cnis", "carta de concessão", "carta", "processo administrativo"]),
        ],
    ),
    Dimension(
        "historico", "Histórico",
        ("filiação", "filiacao", "vínculo", "vinculo", "contribuição", "contribuicao", "carência", "carencia", "cnis", "qualidade de segurado", "qualidade"),
        [
            MatrixItem("linha_tempo", "Linha temporal com lacunas e divergências?", ["cnis", "ctps", "guias", "extrato"]),
        ],
    ),
    Dimension(
        "requerimento", "Requerimento",
        ("der", "requerimento", "decisão administrativa", "decisao", "ciência", "ciencia", "recurso", "protocolo"),
        [
            MatrixItem("cronologia", "DER, decisão, ciência e recurso?", ["protocolo", "carta", "decisão", "decisao"]),
        ],
    ),
    Dimension(
        "incapacidade", "Incapacidade",
        ("incapacidade", "atestado", "perícia", "pericia", "dii", "laudo", "afastamento", "doença", "doenca"),
        [
            MatrixItem("matriz", "Atestados, perícias e duração com fonte?", ["atestado", "laudo", "perícia", "pericia"]),
        ],
    ),
    Dimension(
        "dependencia", "Dependência",
        ("dependente", "dependência", "dependencia", "óbito", "obito", "pensão por morte", "pensao", "idade", "união estável", "uniao"),
        [
            MatrixItem("requisitos", "Vínculo, idade e dependência por benefício?", ["certidão", "certidao", "documento"]),
        ],
    ),
    Dimension(
        "valor", "Valor",
        ("salário de contribuição", "salario", "renda mensal", "teto", "índice", "indice", "reajuste", "retroativo", "atrasado"),
        [
            MatrixItem("cenario", "Salários, índices, períodos e teto?", ["cnis", "memória de cálculo", "memoria", "extrato"]),
        ],
    ),
]
