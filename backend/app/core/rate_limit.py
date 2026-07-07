import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit por IP com janela fixa de 60s no Redis.

    Se o Redis estiver indisponível (ex.: testes locais), o middleware
    deixa as requisições passarem em vez de derrubar a API.
    """

    def __init__(self, app):
        super().__init__(app)
        self._redis = None
        if aioredis is not None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        if self._redis is None:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        window = int(time.time() // 60)
        key = f"ratelimit:{ip}:{window}"
        try:
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, 60)
        except Exception:
            return await call_next(request)

        if count > settings.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Limite de requisições excedido. Tente novamente em instantes."},
            )
        return await call_next(request)
