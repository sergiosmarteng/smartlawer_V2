"""Módulo previdenciário v1.0 (Onda 1B, spec §8)."""

from app.modules.social_security.module import (
    DESCRIPTOR,
    SOCIAL_SECURITY_SOURCES,
    SocialSecurityModule,
    assess_dimension,
    beneficio_cenario,
    register_calculation_rules,
)

__all__ = [
    "DESCRIPTOR",
    "SOCIAL_SECURITY_SOURCES",
    "SocialSecurityModule",
    "assess_dimension",
    "beneficio_cenario",
    "register_calculation_rules",
]
