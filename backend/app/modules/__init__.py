"""Registro de módulos jurídicos por área (V2 §5.2).

O núcleo desconhece regras exclusivas de cada área; cada módulo
fornece esquema, checklist, fontes e avaliadores próprios.
"""

MODULES: dict[str, dict] = {}


def register_module(descriptor: dict) -> dict:
    MODULES[descriptor["module_id"]] = descriptor
    return descriptor


def get_module(module_id: str) -> dict | None:
    return MODULES.get(module_id)
