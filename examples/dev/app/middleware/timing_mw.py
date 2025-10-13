"""
Request timing middleware
"""
import time
from pyjolt.middleware import MiddlewareBase
from pyjolt.request import Request
from pyjolt.response import Response

class TimingMW(MiddlewareBase):

    async def middleware(self, req):
        t0 = time.perf_counter()
        res = await self.next(req)# pass down
        res.headers["x-process-time-ms"] = str(int((time.perf_counter() - t0)*1000))
        return res   
