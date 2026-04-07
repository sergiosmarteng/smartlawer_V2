import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from app.core.config import settings

logger = logging.getLogger(__name__)

class AnalysisResult(BaseModel):
    summary: str = Field(description="Um resumo detalhado e profissional da petição.")
    requests: List[str] = Field(description="Lista de pedidos primários exigidos pelo autor na petição.")
    laws: List[str] = Field(description="Lista de leis, artigos e jurisprudências citadas pelo autor.")
    evidence: str = Field(description="Descrição agregada das provas que o autor diz possuir ou anexa.")
    defense_theses: List[str] = Field(description="Possíveis teses preliminares e de mérito para a defesa usar contra a petição.")

class LegalAnalyzer:
    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        
        if self.provider == "openrouter":
            self.api_key = settings.OPENROUTER_API_KEY
            if not self.api_key:
                logger.warning("OPENROUTER_API_KEY is not set. Inference will fail.")
            self.llm = ChatOpenAI(
                model="anthropic/claude-3-opus", # Default good model on openrouter, or you can switch
                openai_api_base="https://openrouter.ai/api/v1",
                openai_api_key=self.api_key,
                temperature=0.0
            )
        else: # Default is openai
            self.api_key = settings.OPENAI_API_KEY
            if not self.api_key:
                logger.warning("OPENAI_API_KEY is not set. Inference will fail.")
            self.llm = ChatOpenAI(
                model="gpt-4-turbo", 
                temperature=0.0, 
                api_key=self.api_key
            )
            
        self.parser = PydanticOutputParser(pydantic_object=AnalysisResult)
        
    def analyze_petition(self, text: str) -> dict:
        """
        Submete o texto extraído do OCR para LLM analisá-lo e inferir estruturação.
        """
        if not self.api_key:
             raise ValueError("API Key ausente na configuração")

        prompt = PromptTemplate(
            template="""Você é um Especialista de Inteligência Artificial Jurídica de alto padrão (Arquiteto de Defesas do SmartLawer V2).
Sua tarefa é analisar o texto extraído da petição inicial abaixo e organizá-lo.
Extraia: O resumo dos fatos, os pedidos finais do autor, as leis ou artigos invocados, as evidências citadas, e construa 3 ou mais teses preliminares/mérito que a defesa pode usar frente a essas arguições.

{format_instructions}

TEXTO DA PETIÇÃO:
{petition_text}
""",
            input_variables=["petition_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )

        chain = prompt | self.llm | self.parser
        
        try:
            # Invoking Langchain Pipeline
            result: AnalysisResult = chain.invoke({"petition_text": text[:20000]}) # limiting chars just to be safe
            return result.model_dump()
        except Exception as e:
            logger.error(f"Erro no processamento da OpenAI: {e}")
            raise e
