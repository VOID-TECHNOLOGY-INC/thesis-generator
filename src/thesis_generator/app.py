from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from thesis_generator.graph.builder import build_main_graph
from thesis_generator.state import ThesisState


def _coerce_state(result: ThesisState | dict[str, Any]) -> ThesisState:
    return result if isinstance(result, ThesisState) else ThesisState(**result)


def create_app(*, graph_factory: Callable[[], Any] | None = None) -> FastAPI:
    """Construct a FastAPI app that streams LangGraph events."""

    factory = graph_factory or build_main_graph
    app = FastAPI(title="Thesis Generator")

    @app.post("/run")
    async def run(payload: dict[str, Any]) -> StreamingResponse:
        topic = payload.get("topic")
        if not topic:
            raise HTTPException(status_code=400, detail="topic is required")

        target_word_count = int(payload.get("target_word_count", 1200))
        style_guide = str(payload.get("style_guide", "apa"))

        state = ThesisState(
            topic=topic,
            target_word_count=target_word_count,
            style_guide=style_guide,
        )
        graph = factory()

        async def event_stream():
            try:
                async for event in graph.astream_events(state):
                    yield json.dumps(event) + "\n"
            except AttributeError:
                # fallback: run synchronously if streaming not supported
                final = _coerce_state(graph.invoke(state))
                yield json.dumps({"event": "complete", "data": final.model_dump()}) + "\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


async def serve_app(app: FastAPI, *, host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run a development server inside an async context."""

    import uvicorn

    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


__all__ = ["create_app", "serve_app"]
