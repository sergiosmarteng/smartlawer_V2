"""Shared OpenAI-compatible client factory.

Pinned truth (2026-09): the image ships ``openai==1.30.5`` with
``httpx==0.28``. httpx 0.28 removed the ``proxies`` keyword, which
openai 1.30.x still passes when it builds its own HTTP client — so
``OpenAI(...)`` raises
``Client.__init__() got an unexpected keyword argument 'proxies'``.
Passing an explicitly built ``httpx.Client`` sidesteps the broken
combination with no image rebuild. If the pins ever change, this is
the single place to revisit.
"""
import logging

logger = logging.getLogger(__name__)


def build_client(api_key: str, base_url: str | None = None):
    """Build an OpenAI-compatible client that survives the httpx skew."""
    from openai import OpenAI
    import httpx

    kwargs: dict = {"api_key": api_key, "http_client": httpx.Client()}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)
