"""
Request timing middleware
"""
from typing import TYPE_CHECKING
import time
from pyjolt.middleware import MiddlewareBase

if TYPE_CHECKING:
    from pyjolt.request import Request
    from pyjolt.response import Response

class TimingMW(MiddlewareBase):

    async def middleware(self, req: "Request") -> "Response":
        t0 = time.perf_counter()
        res = await self.next(req)# pass down
        res.headers["x-process-time-ms"] = str(int((time.perf_counter() - t0)*1000))
        return res
