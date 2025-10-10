"""
Request timing middleware
"""
import time
from pyjolt.middleware_base import MiddlewareBase
from pyjolt.request import Request
from pyjolt.response import Response

class TimingMW(MiddlewareBase):
    async def __call__(self, req: Request) -> Response:
        t0 = time.perf_counter()
        res = await self.next_app(req)           # pass down
        res.headers["x-process-time-ms"] = str(int((time.perf_counter() - t0)*1000))
        return res
