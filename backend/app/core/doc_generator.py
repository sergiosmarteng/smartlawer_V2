import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate

from app.core.action_plan import build_action_plan


class DocxGenerator:
    DEFAULT_TEXT = "Nao informado."

    #: Context keys produced by ``_normalize_analysis_context`` — the only
    #: variable roots a user template may reference (C1/BL-015).
    SUPPORTED_CONTEXT_KEYS = frozenset(
        {
            "summary",
            "requests",
            "laws",
            "evidence",
            "defense_theses",
            "generatedDefenseStrategy",
            "analysis_json",
        }
    )

    _XML_TAG_RE = re.compile(r"<[^>]+>")
    _JINJA_VAR_RE = re.compile(r"\{\{\s*(.*?)\s*\}\}", re.DOTALL)
    _JINJA_TAG_RE = re.compile(r"\{%\s*(.*?)\s*%\}", re.DOTALL)
    _IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    _STRING_LITERAL_RE = re.compile(r"'[^']*'|\"[^\"]*\"")
    _LOOP_VAR_RE = re.compile(
        r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)\s+in\b"
    )
    _SET_VAR_RE = re.compile(r"\bset\s+([A-Za-z_][A-Za-z0-9_]*)")
    #: Jinja control words and test names that are not context variables.
    _JINJA_KEYWORDS = frozenset(
        {
            "for", "in", "if", "elif", "else", "endif", "endfor", "and",
            "or", "not", "is", "none", "true", "false", "loop", "set",
            "macro", "endmacro", "call", "endcall", "filter", "endfilter",
            "do", "import", "from", "as", "recursive", "scoped", "with",
            "without", "trans", "endtrans", "raw", "endraw", "extends",
            "block", "endblock", "include", "autoescape", "endautoescape",
            # Jinja test names (``x is <test>``) — never context keys.
            "defined", "undefined", "callable", "sequence", "mapping",
            "iterable", "number", "integer", "float", "string", "odd",
            "even", "divisibleby", "eq", "equalto", "ne", "lt", "lessthan",
            "le", "gt", "greaterthan", "ge", "sameas", "lower", "upper",
            "escaped",
        }
    )

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
            # V2 T12/D06: plano de atuação, não cópia das teses.
            "generatedDefenseStrategy": build_action_plan(
                {
                    "defense_theses": normalized_defense_theses,
                    "requests": normalized_requests,
                    "laws": normalized_laws,
                }
            ),
            "analysis_json": json.dumps(analysis_dict, ensure_ascii=True, default=str),
        }

    @classmethod
    def _expression_roots(cls, expression: str) -> set[str]:
        """Root variable names referenced by one Jinja expression.

        String literals are blanked first; ``|filter`` / ``|filter(args)``
        segments are dropped (only the value head can be a context key).
        """
        cleaned = cls._STRING_LITERAL_RE.sub("", expression)
        cleaned = cleaned.split("|", 1)[0]
        roots: set[str] = set()
        for match in cls._IDENTIFIER_RE.finditer(cleaned):
            token = match.group(0)
            start = match.start()
            # Attribute access (``foo.bar``): only the head ``foo`` counts.
            if start > 0 and cleaned[start - 1] == ".":
                continue
            if token.lower() in cls._JINJA_KEYWORDS:
                continue
            roots.add(token)
        return roots

    @classmethod
    def _template_locals(cls, tag_body: str) -> set[str]:
        """Variables a ``{% %}`` tag defines (loop/set targets)."""
        locals_: set[str] = set()
        for match in cls._LOOP_VAR_RE.finditer(tag_body):
            for name in match.group(1).split(","):
                locals_.add(name.strip())
        for match in cls._SET_VAR_RE.finditer(tag_body):
            locals_.add(match.group(1))
        return locals_

    @classmethod
    def discover_placeholders(cls, template_path: str) -> list[str]:
        """List ``{{roots}}`` referenced by a DOCX template.

        Pure stdlib (zipfile + regex over every ``word/*.xml`` part) so
        discovery behaves identically in tests and production, with no new
        dependencies. XML tags are stripped before matching, which also
        rejoins Jinja tags split across ``<w:t>`` runs.
        """
        template = Path(template_path)
        if not template.exists():
            raise FileNotFoundError(f"Template nao encontrado em: {template_path}")
        if template.suffix.lower() != ".docx":
            raise ValueError(f"Template invalido para geracao DOCX: {template_path}")

        try:
            archive = zipfile.ZipFile(str(template))
        except zipfile.BadZipFile as exc:
            raise ValueError(
                f"Arquivo nao e um DOCX valido: {template_path}"
            ) from exc

        roots: set[str] = set()
        defined_locals: set[str] = set()
        with archive:
            part_names = [
                name
                for name in archive.namelist()
                if name.startswith("word/") and name.endswith(".xml")
            ]
            if "word/document.xml" not in part_names:
                raise ValueError(
                    f"Arquivo nao e um DOCX valido: {template_path}"
                )
            for part_name in part_names:
                try:
                    raw_text = archive.read(part_name).decode("utf-8", errors="replace")
                except KeyError:
                    continue
                visible_text = cls._XML_TAG_RE.sub("", raw_text)
                for match in cls._JINJA_TAG_RE.finditer(visible_text):
                    tag_body = match.group(1)
                    defined_locals.update(cls._template_locals(tag_body))
                    roots.update(cls._expression_roots(tag_body))
                for match in cls._JINJA_VAR_RE.finditer(visible_text):
                    roots.update(cls._expression_roots(match.group(1)))

        roots -= defined_locals
        return [f"{{{{{root}}}}}" for root in sorted(roots)]

    @classmethod
    def unsupported_placeholders(cls, placeholders: list[str] | None) -> list[str]:
        """Subset of discovered ``{{roots}}`` with no normalized context key."""
        unsupported: list[str] = []
        for placeholder in placeholders or []:
            root = placeholder.strip().strip("{}").strip()
            if root and root not in cls.SUPPORTED_CONTEXT_KEYS:
                unsupported.append(placeholder)
        return unsupported

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
