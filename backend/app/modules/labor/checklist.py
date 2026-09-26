"""Matriz de acidente do trabalho (V2 §10.1).

Sete dimensões; cada item declara o que deve existir como prova e o
que fazer quando só há alegação. Alegação não é prova (§4).
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
    items: list[MatrixItem]


WORK_ACCIDENT_MATRIX: list[Dimension] = [
    Dimension(
        "relacao_trabalho", "Relação de trabalho",
        [
            MatrixItem("funcao", "Função e tarefas efetivas?", ["registro", "ctps", "testemunha"]),
            MatrixItem("admissao", "Data de admissão?", ["ctps", "contracheque"]),
            MatrixItem("remuneracao", "Remuneração e composição?", ["contracheque", "cct"]),
            MatrixItem("empregador", "Empregador identificado?", ["cnpj", "contrato"]),
        ],
    ),
    Dimension(
        "evento", "Evento",
        [
            MatrixItem("data_local", "Data e local do evento?", ["cat", "boletim", "testemunha"]),
            MatrixItem("dinamica", "Dinâmica alegada?", ["fotos", "pericia_seguranca", "testemunha"]),
            MatrixItem("equipamento", "Equipamento/agente envolvido?", ["manual", "manutencao", "fotos"]),
        ],
    ),
    Dimension(
        "seguranca", "Segurança",
        [
            MatrixItem("treinamento", "Treinamento comprovado?", ["ficha_treinamento", "certificado"]),
            MatrixItem("protecao", "Proteções coletivas/individuais na data?", ["ficha_epi", "inspecao", "fotos"]),
            MatrixItem("manutencao", "Manutenção documentada?", ["ordens_servico", "checklist"]),
            MatrixItem("norma_temporal", "Redação da norma vigente à época?", ["nr_historica"]),
        ],
    ),
    Dimension(
        "nexo_dano", "Nexo e dano",
        [
            MatrixItem("lesao", "Lesão narrada e evolução?", ["prontuario", "laudo"]),
            MatrixItem("afastamento", "Afastamentos e benefício?", ["carta_concessao", "comunicacao_previdenciaria"]),
            MatrixItem("incapacidade", "Incapacidade alegada x periciada?", ["pericia_medica"]),
        ],
    ),
    Dimension(
        "responsabilidade", "Responsabilidade",
        [
            MatrixItem("objetiva", "Requisitos da objetiva (risco especial habitual)?", ["prova_risco", "precedente"]),
            MatrixItem("subjetiva", "Conduta, dano e nexo (culpa)?", ["documentos_seguranca", "testemunha"]),
            MatrixItem("excludentes", "Excludente com base fática investigável?", ["prova_contraria"]),
        ],
    ),
    Dimension(
        "reparacao", "Reparação",
        [
            MatrixItem("material", "Dano material/lucros cessantes discriminados?", ["memoria_calculo"]),
            MatrixItem("pensao", "Pensão: termo inicial, duração e base?", ["sentenca_parametros", "pericia"]),
            MatrixItem("moral_estetico", "Dano moral/estético fundamentado?", ["fotos", "laudo"]),
            MatrixItem("coletiva", "CCT: vigência, cláusula e fato gerador?", ["cct_integral"]),
            MatrixItem("sobreposicao", "Sobreposição entre rubricas?", ["memoria_calculo"]),
        ],
    ),
    Dimension(
        "processo", "Processo",
        [
            MatrixItem("competencia", "Competência?", ["distribuicao"]),
            MatrixItem("gratuidade", "Gratuidade: fundamento e alcance temporal?", ["declaracao", "contracheque"]),
            MatrixItem("honorarios", "Honorários: base futura?", ["pedido"]),
            MatrixItem("prova_pericial", "Perícia requerida x realizada?", ["requerimento", "laudo"]),
        ],
    ),
]


@dataclass
class MatrixResult:
    dimension: str
    item: str
    status: str  # documented | alleged | missing
    source_refs: list[str] = field(default_factory=list)
    impact: str = ""
    action: str = ""


def evaluate_matrix(
    extracted: dict[str, dict[str, list[str]]],
    *,
    impact_for_missing: str = "Lacuna probatória: tese depende de prova ainda não localizada.",
    action_for_missing: str = "Incluir em diligências e quesitos.",
) -> list[MatrixResult]:
    """Cruza matriz x refs extraídas (alegação ≠ prova, §4).

    ``extracted``: {dimensão: {item: [source_refs]}}. Sem refs, o item
    é lacuna — nunca fato confirmado.
    """
    results: list[MatrixResult] = []
    for dimension in WORK_ACCIDENT_MATRIX:
        items_refs = extracted.get(dimension.key, {})
        for item in dimension.items:
            item_refs = list(items_refs.get(item.key, []))
            if item_refs:
                results.append(
                    MatrixResult(
                        dimension.key, item.key, "documented",
                        source_refs=item_refs,
                        impact="Suportado por fonte do conjunto.",
                        action="Conferir aderência ao pedido afetado.",
                    )
                )
            else:
                results.append(
                    MatrixResult(
                        dimension.key, item.key, "missing",
                        impact=impact_for_missing, action=action_for_missing,
                    )
                )
    return results
