import json
import logging
import re
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger("http")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {"ts": datetime.now(timezone.utc).isoformat(), "level": record.levelname,
                "logger": record.name, "msg": record.getMessage()}
        data.update(getattr(record, "fields", {}))
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").disabled = True  # replaced by our own request log


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self.counters: dict[str, int] = defaultdict(int)
            self.latencies: deque = deque(maxlen=1000)
            self.latency_sum = 0.0
            self.started = time.time()

    def inc(self, name: str, n: int = 1) -> None:
        with self._lock:
            self.counters[name] += n

    def observe_request(self, status: int, ms: float) -> None:
        with self._lock:
            self.counters["requests_total"] += 1
            if status >= 500:
                self.counters["errors_total"] += 1
            elif status >= 400:
                self.counters["client_errors_total"] += 1
            self.latency_sum += ms
            self.latencies.append(ms)

    def snapshot(self) -> dict:
        with self._lock:
            c = self.counters
            total = c["requests_total"]
            ordered = sorted(self.latencies)
            p95 = ordered[int(0.95 * (len(ordered) - 1))] if ordered else 0.0
            return {
                "requests_total": total,
                "errors_total": c["errors_total"],
                "client_errors_total": c["client_errors_total"],
                "avg_latency_ms": round(self.latency_sum / total, 2) if total else 0.0,
                "p95_latency_ms": round(p95, 2),
                "llm_calls": c["llm_calls"],
                "llm_failures": c["llm_failures"],
                "llm_fallbacks": c["llm_fallbacks"],
                "llm_input_tokens": c["llm_input_tokens"],
                "llm_output_tokens": c["llm_output_tokens"],
                "uptime_seconds": int(time.time() - self.started),
            }


metrics = Metrics()
_RID = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def install_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def observe(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if _RID.match(incoming) else uuid.uuid4().hex[:12]
        request.state.user_id = None
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception("unhandled_error", extra={"fields": {"request_id": request_id}})
            response = JSONResponse({"detail": "Internal server error"}, status_code=500)
        ms = (time.perf_counter() - start) * 1000
        route = getattr(request.scope.get("route"), "path", request.url.path)
        metrics.observe_request(response.status_code, ms)
        response.headers["x-request-id"] = request_id
        log.info("request", extra={"fields": {
            "request_id": request_id, "user_id": request.state.user_id, "route": route,
            "method": request.method, "status": response.status_code, "latency_ms": round(ms, 2)}})
        return response
