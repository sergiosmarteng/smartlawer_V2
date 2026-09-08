import logging

from sqlalchemy.orm import Session

from app.models.prompt_profile import PromptProfile

logger = logging.getLogger(__name__)


def get_default_profile(db: Session, *, user_id) -> PromptProfile | None:
    return (
        db.query(PromptProfile)
        .filter(PromptProfile.user_id == user_id, PromptProfile.is_default.is_(True))
        .order_by(PromptProfile.created_at.desc())
        .first()
    )


def get_default_strategy_prompt(db: Session, *, user_id) -> str | None:
    """Extra AI guidance for the user's default profile, if any.

    Never raises: the ingestion worker must survive profile issues and
    fall back to the default prompt.
    """
    try:
        profile = get_default_profile(db, user_id=user_id)
        if profile and (profile.strategy_prompt or "").strip():
            return profile.strategy_prompt.strip()
    except Exception as exc:
        logger.warning("Ignoring prompt profile lookup failure: %s", exc)
    return None


def set_default_profile(db: Session, *, profile: PromptProfile) -> PromptProfile:
    (db.query(PromptProfile)
        .filter(PromptProfile.user_id == profile.user_id,
                PromptProfile.id != profile.id)
        .update({PromptProfile.is_default: False}))
    profile.is_default = True
    db.commit()
    db.refresh(profile)
    return profile
