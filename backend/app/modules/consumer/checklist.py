"""Matriz do consumidor (Onda 1B, spec §7). Seis temas."""

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


CONSUMER_MATRIX: list[Dimension] = [
    Dimension(
        "relacao_consumo", "Relação de consumo",
        ("consumidor", "fornecedor", "produto", "serviço", "servico", "cadeia", "destinatário", "destinatario"),
        [
            MatrixItem("papeis", "Fornecedor, consumidor e cadeia identificados?", ["contrato", "nota fiscal", "cadastro"]),
        ],
    ),
    Dimension(
        "oferta_contrato", "Oferta e contrato",
        ("oferta", "publicidade", "preço", "preco", "aceite", "condições", "condicoes", "alteração", "alteracao", "print", "conversa", "aplicativo", "anúncio", "anuncio"),
        [
            MatrixItem("comparacao", "Oferta x execução comparadas?", ["anúncio", "anuncio", "print", "contrato"]),
        ],
    ),
    Dimension(
        "vicio_defeito", "Vício/defeito",
        ("vício", "vicio", "defeito", "dano", "comunicação", "comunicacao", "garantia", "assistência", "assistencia"),
        [
            MatrixItem("prova", "Evento, natureza e tentativas de solução?", ["protocolo", "laudo", "foto", "nota"]),
        ],
    ),
    Dimension(
        "cobranca", "Cobrança",
        ("fatura", "cobrança", "cobranca", "pagamento", "estorno", "negativação", "negativacao", "débito", "debito"),
        [
            MatrixItem("valores", "Faturas, pagamentos e estornos verificáveis?", ["fatura", "comprovante", "extrato"]),
        ],
    ),
    Dimension(
        "atendimento", "Atendimento",
        ("protocolo", "atendimento", "ouvidoria", "prazo de resposta", "tentativa extrajudicial"),
        [
            MatrixItem("trilha", "Trilha extrajudicial documentada?", ["protocolo", "e-mail", "email", "carta"]),
        ],
    ),
    Dimension(
        "dados_plataforma", "Dados e plataforma",
        ("dados pessoais", "lgpd", "plataforma", "intermediário", "intermediario", "segurança", "seguranca", "vazamento", "print", "conversa", "conta", "captura"),
        [
            MatrixItem("tratamento", "Tratamento e intermediários mapeados?", ["política", "politica", "termo", "log"]),
        ],
    ),
]
