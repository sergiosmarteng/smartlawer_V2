import json
import os
import tempfile
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate


class DocxGenerator:
    DEFAULT_TEXT = "Nao informado."

    @classmethod
    def _stringify_value(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            parts = []
            for key, item in value.items():
                rendered_item = cls._stringify_value(item)
                if rendered_item:
                    parts.append(f"{key}: {rendered_item}")
            return "\n".join(parts)
        if isinstance(value, (list, tuple, set)):
            parts = [cls._stringify_value(item) for item in value]
            return "\n".join(part for part in parts if part)
        return str(value).strip()

    @classmethod
    def _coerce_text(cls, value: Any, *, default: str | None = None) -> str:
        rendered = cls._stringify_value(value)
        if rendered:
            return rendered
        return default or cls.DEFAULT_TEXT

    @classmethod
    def _coerce_list(
        cls,
        value: Any,
        *,
        fallback_label: str,
    ) -> list[str]:
        items: list[str] = []

        if isinstance(value, dict):
            for key, item in value.items():
                rendered_item = cls._stringify_value(item)
                if rendered_item:
                    items.append(f"{key}: {rendered_item}")
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                rendered_item = cls._stringify_value(item)
                if rendered_item:
                    items.append(rendered_item)
        else:
            rendered_item = cls._stringify_value(value)
            if rendered_item:
                if "\n" in rendered_item:
                    items.extend(
                        line.strip("- ").strip()
                        for line in rendered_item.splitlines()
                        if line.strip()
                    )
                else:
                    items.append(rendered_item)

        normalized_items = [item for item in items if item]
        if normalized_items:
            return normalized_items
        return [fallback_label]

    @classmethod
    def _normalize_analysis_context(cls, analysis_dict: dict[str, Any]) -> dict[str, Any]:
        generated_strategy = analysis_dict.get("generatedDefenseStrategy")
        defense_theses = analysis_dict.get("defense_theses", generated_strategy)
        requests = analysis_dict.get("requests", analysis_dict.get("keyArguments"))

        normalized_summary = cls._coerce_text(analysis_dict.get("summary"))
        normalized_requests = cls._coerce_list(
            requests,
            fallback_label="Nenhum pedido identificado na analise disponivel.",
        )
        normalized_laws = cls._coerce_list(
            analysis_dict.get("laws"),
            fallback_label="Nenhuma fundamentacao legal estruturada foi extraida.",
        )
        normalized_evidence = cls._coerce_text(
            analysis_dict.get("evidence"),
            default="Nenhuma prova estruturada foi identificada.",
        )
        normalized_defense_theses = cls._coerce_list(
            defense_theses,
            fallback_label="Nenhuma tese defensiva estruturada foi sugerida.",
        )

        return {
            "summary": normalized_summary,
            "requests": normalized_requests,
            "laws": normalized_laws,
            "evidence": normalized_evidence,
            "defense_theses": normalized_defense_theses,
            "generatedDefenseStrategy": "\n".join(
                f"{index + 1}. {item}"
                for index, item in enumerate(normalized_defense_theses)
            ),
            "analysis_json": json.dumps(analysis_dict, ensure_ascii=True, default=str),
        }

    @staticmethod
    def generate_defense(analysis_dict: dict, template_path: str) -> str:
        """
        Le um documento de Word (.docx) contendo tags do Jinja e injeta os dados da analise.
        """
        template = Path(template_path)
        if not template.exists():
            raise FileNotFoundError(f"Template nao encontrado em: {template_path}")

        if template.suffix.lower() != ".docx":
            raise ValueError(f"Template invalido para geracao DOCX: {template_path}")

        normalized_context = DocxGenerator._normalize_analysis_context(analysis_dict or {})

        try:
            doc = DocxTemplate(str(template))
        except Exception as exc:
            raise RuntimeError(
                f"Nao foi possivel abrir o template DOCX em '{template_path}'"
            ) from exc

        try:
            doc.render(normalized_context)
        except Exception as exc:
            raise RuntimeError(
                "Falha ao renderizar o DOCX com o payload de analise normalizado"
            ) from exc

        fd, output_file = tempfile.mkstemp(
            suffix=".docx",
            prefix="defesa_gerada_",
            dir=tempfile.gettempdir(),
        )
        os.close(fd)

        try:
            doc.save(output_file)
        except Exception as exc:
            raise RuntimeError(
                f"Falha ao salvar o DOCX gerado em '{output_file}'"
            ) from exc

        return output_file
