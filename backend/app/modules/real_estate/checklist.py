"""Matriz imobiliária (Onda 2B, spec §7). Seis temas."""

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


REAL_ESTATE_MATRIX: list[Dimension] = [
    Dimension(
        "imovel", "Imóvel",
        ("matrícula", "matricula", "endereço", "endereco", "área", "area", "unidade", "cadastro", "terreno", "lote"),
        [
            MatrixItem("identidade", "Matrícula, endereço e área com divergências?", ["matrícula", "matricula", "certidão", "certidao", "planta"]),
        ],
    ),
    Dimension(
        "direito", "Direito",
        ("propriedade", "posse", "promessa", "usufruto", "garantia", "locação", "locacao", "domínio", "dominio", "direito real"),
        [
            MatrixItem("linha", "Propriedade, posse e promessa distinguidos?", ["escritura", "contrato", "registro"]),
        ],
    ),
    Dimension(
        "registro", "Registro",
        ("registro", "matrícula", "matricula", "imóvel", "imovel", "averbação", "averbacao", "prenotação", "prenotacao", "ônus", "onus", "certidão", "certidao", "cartório", "cartorio"),
        [
            MatrixItem("estado", "Atos, ônus e certidões com data?", ["certidão atualizada", "certidao", "matrícula", "matricula"]),
        ],
    ),
    Dimension(
        "negocio", "Negócio",
        ("preço", "preco", "parcela", "entrega", "escritura", "financiamento", "sinal", "pagamento"),
        [
            MatrixItem("obrigacoes", "Preço, parcelas, entrega e escritura?", ["contrato", "recibo", "comprovante", "financiamento"]),
        ],
    ),
    Dimension(
        "conflito", "Conflito",
        ("limite", "divisa", "benfeitoria", "atraso", "vício", "vicio", "inadimplemento", "despejo", "litígio", "litigio"),
        [
            MatrixItem("fatos", "Fatos, prova e alternativas mapeados?", ["vistoria", "foto", "laudo", "testemunha"]),
        ],
    ),
    Dimension(
        "urbanismo", "Urbanismo",
        ("zoneamento", "uso do solo", "aprovação", "aprovacao", "regularização", "regularizacao", "condomínio", "condominio", "prefeitura", "habite-se", "habite"),
        [
            MatrixItem("fonte", "Fonte municipal/registral e pendências?", ["lei municipal", "certidão", "certidao", "alvará", "alvara"]),
        ],
    ),
]
