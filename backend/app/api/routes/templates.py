import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.document import get_document
from app.core.doc_generator import DocxGenerator

router = APIRouter()

# Pasta onde ficam os originais do escritorio
TEMPLATE_DIR = os.path.join(os.getcwd(), "backend", "templates")
BASE_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "base_template.docx")

@router.get("/{document_id}/generate")
def generate_docx_document(
    document_id: str,
    db: Session = Depends(deps.get_db),
    # Descomente a linha abaixo quando for travar a rota com auth:
    # current_user = Depends(deps.get_current_active_user) 
):
    """
    Dada a extração/análise de um documento prévio, gera a documentação do word cruzada
    e emite num Attachment Stream pro usuário salvar fisicamente no PC.
    """
    doc = get_document(db, id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento original não encontrado")

    if not doc.analysis:
        raise HTTPException(status_code=400, detail="Processo OpenAI ainda não gerou as teses ou falhou. Tente novamente.")
    
    # Extrai as informações serializando as colunas (summary, laws, requests, type)
    # Como as tipagens do Pydantic gravam arrays nas colunas JSON do Analysis, temos conversoes lisas
    analysis_data = {
        "summary": doc.analysis[0].summary,
        "requests": doc.analysis[0].requests,
        "laws": doc.analysis[0].laws,
        "evidence": doc.analysis[0].evidence,
        "defense_theses": doc.analysis[0].defense_theses
    }

    try:
        # Puxa o template local
        output_path = DocxGenerator.generate_defense(analysis_dict=analysis_data, template_path=BASE_TEMPLATE_PATH)
        
        return FileResponse(
            path=output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"Defesa_{doc.id}.docx"
        )
    except FileNotFoundError:
         raise HTTPException(status_code=500, detail="A Base Documental (.docx template) do sistema não foi localizada.")
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erro interno de geração do DOCX: {str(e)}")
