"""Tokens de matrícula do agente desktop.

O administrador gera um token de curta duração no dashboard; o agente o
usa uma única vez para se registrar e receber seu token permanente.
Armazenado no Redis com TTL; em ambientes sem Redis (testes) usa um
dicionário em memória.
"""

import secrets
import time

from app.core.config import settings

ENROLLMENT_TTL_SECONDS = 15 * 60

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None

_memory_store: dict[str, tuple[str, float]] = {}
_redis = None


def _get_redis():
    global _redis
    if _redis is None and aioredis is not None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def create_enrollment_token(org_id: str) -> str:
    token = secrets.token_urlsafe(32)
    r = _get_redis()
    if r is not None:
        try:
            await r.set(f"enroll:{token}", org_id, ex=ENROLLMENT_TTL_SECONDS)
            return token
        except Exception:
            pass
    _memory_store[token] = (org_id, time.time() + ENROLLMENT_TTL_SECONDS)
    return token


async def consume_enrollment_token(token: str) -> str | None:
    """Valida e invalida o token, retornando o org_id ou None."""
    r = _get_redis()
    if r is not None:
        try:
            key = f"enroll:{token}"
            org_id = await r.get(key)
            if org_id:
                await r.delete(key)
            return org_id
        except Exception:
            pass
    entry = _memory_store.pop(token, None)
    if entry is None or entry[1] < time.time():
        return None
    return entry[0]
