import os
import tempfile
from docxtpl import DocxTemplate

class DocxGenerator:
    @staticmethod
    def generate_defense(analysis_dict: dict, template_path: str) -> str:
        """
        Lê um documento de Word (.docx) contendo as tags do Jinja (ex: {{ summary }})
        E substitui os valores reais injetando os dados da análise.
        Retorna o caminho físico do arquivo temporário gerado para download.
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template não encontrado em: {template_path}")

        # Inicia e lê o esqueleto padrão do word
        doc = DocxTemplate(template_path)
        
        # Faz o cruzamento das varíaveis do dict e injeta no .docx
        doc.render(analysis_dict)
        
        # Cria um arquivo estático e temporario
        temp_dir = tempfile.gettempdir()
        output_file = os.path.join(temp_dir, "defesa_gerada.docx")
        
        doc.save(output_file)
        return output_file
