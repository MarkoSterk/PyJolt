"""
Timing middleware
"""
import time
from pyjolt import Request, Response
from pyjolt.middleware import MiddlewareBase

class TimingMW(MiddlewareBase):
    """Timing middleware handler"""
    async def middleware(self, req: Request) -> Response:
        t0: float = time.perf_counter()
        res = await self.next(req) # pass down
        self.app.logger.info(
            "PERFORMANCE: Request to "
            f"{req.path}?{req.query_string} "
            f"took {int((time.perf_counter() - t0)*1000)} ms"
        )
        return res
