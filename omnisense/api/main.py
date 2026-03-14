"""
OmniSense API - Orchestration layer for sensory agents powered by Gemini.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from pydantic import BaseModel, Field

from orchestrator.agent_runtime import AgentRuntime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("omnisense-api")

# Pydantic Models for Response Validation


class VisionResponse(BaseModel):
    """Schema for vision analysis response."""

    scene: str
    hazard: str
    guidance: str
    safety_level: str


class AudioResponse(BaseModel):
    """Schema for audio analysis response."""

    sound_event: str
    urgency: str
    guidance: str


class NavigationResponse(BaseModel):
    """Schema for navigation guidance response."""

    direction: str
    landmark: str
    caution: str
    progress: str


class HealthStatus(BaseModel):
    """Schema for health check response."""

    status: str
    version: str


app = FastAPI(
    title="OmniSense API",
    description="Advanced Accessibility Orchestrator powered by Gemini",
    version="1.1.0",
)

# Global instances
RUNNERS: Dict[str, Runner] = {}
SESSION_SERVICE = InMemorySessionService()
RUNTIME: Optional[AgentRuntime] = None

# Initialize Orchestrator
try:
    RUNTIME = AgentRuntime()
    # Initialize ADK Runners for each agent
    for agent in RUNTIME.get_adk_agents():
        if agent:
            RUNNERS[agent.name] = Runner(
                agent=agent,
                app_name="OmniSense",
                session_service=SESSION_SERVICE,
            )
        else:
            logger.warning("Skipping Runner initialization for null agent (Mock Mode).")
    logger.info("Orchestrator runtime and %d ADK runners initialized.", len(RUNNERS))
except (ImportError, ValueError, RuntimeError) as e:
    logger.critical("Failed to initialize AgentRuntime or Runners: %s", e)
except Exception as e:  # pylint: disable=broad-except
    logger.critical("Unexpected error during initialization: %s", e)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc):
    """Handle Pydantic validation errors."""
    logger.error("Validation Error: %s", exc.errors())
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


# Mount static files and React build
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/", include_in_schema=False)
    async def read_index():
        """Serve the React frontend index."""
        return FileResponse("frontend/dist/index.html")

else:
    # Fallback to legacy mobile UI
    app.mount("/static", StaticFiles(directory="mobile"), name="static")

    @app.get("/", include_in_schema=False)
    async def read_index():
        """Serve the legacy mobile index."""
        return FileResponse("mobile/index.html")


@app.on_event("startup")
async def startup_event():
    """Startup tasks."""
    if RUNTIME:
        # Initialize the centralized ADK session for the runtime
        await RUNTIME.initialize_sessions()
    logger.info("OmniSense API Startup complete.")


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """System health check endpoint."""
    return HealthStatus(status="healthy", version="1.1.0")


# A2A Protocol Discovery Endpoint


@app.get("/.well-known/agent.json")
async def get_agent_card():
    """A2A discovery endpoint returning the agent card."""
    logger.info("A2A Discovery request received. Runners: %s", list(RUNNERS.keys()))

    # Try to get VisionAgent, or fallback to the first available runner
    agent_runner = RUNNERS.get("VisionAgent") or (
        next(iter(RUNNERS.values())) if RUNNERS else None
    )

    if not agent_runner:
        logger.error("No runners initialized for A2A discovery")
        raise HTTPException(
            status_code=500, detail="No agents initialized for A2A discovery"
        )

    primary_agent = agent_runner.agent

    # Try to load the detailed JSON card metadata
    metadata = {}
    card_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "agents",
            "cards",
            "VisionAgent_Card.json",
        )
    )
    if os.path.exists(card_path):
        try:
            with open(card_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning("Could not parse agent card metadata.")

    return {
        "name": metadata.get("name", primary_agent.name),
        "description": metadata.get("description", primary_agent.description),
        "mission": metadata.get("mission", ""),
        "capabilities": metadata.get("capabilities", []),
        "version": "1.2.0",
        "endpoints": {"run": "/run"},
    }


# A2A Protocol Execution Endpoint


class A2ARunRequest(BaseModel):
    """Schema for A2A execution request."""

    user_id: str = Field(..., alias="user_id")
    session_id: str = Field(..., alias="session_id")
    new_message: Optional[str] = Field(None, alias="new_message")
    invocation_id: Optional[str] = Field(None, alias="invocation_id")
    state_delta: Optional[Dict[str, Any]] = Field(None, alias="state_delta")


@app.post("/run")
async def run_agent_a2a(req: A2ARunRequest):
    """A2A execution endpoint."""
    # Route to VisionAgent by default for A2A
    runner = RUNNERS.get("VisionAgent")
    if not runner or not runner.agent:
        raise HTTPException(
            status_code=500, detail="VisionAgent runner not initialized"
        )

    async def event_generator():
        session = await SESSION_SERVICE.get_session(
            app_name="OmniSense",
            user_id=req.user_id,
            session_id=req.session_id,
        )
        if not session:
            logger.info(
                "Creating new session for user %s, session %s",
                req.user_id,
                req.session_id,
            )
            await SESSION_SERVICE.create_session(
                app_name="OmniSense",
                user_id=req.user_id,
                session_id=req.session_id,
            )

        # Runner.run_async expects a Content object for new_message
        new_msg = None
        if req.new_message:
            new_msg = genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=req.new_message)],
            )

        async for event in runner.run_async(
            user_id=req.user_id,
            session_id=req.session_id,
            new_message=new_msg,
            invocation_id=req.invocation_id,
            state_delta=req.state_delta,
        ):
            yield f"data: {event.model_dump_json(exclude_none=True, by_alias=True)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/analyze_scene", response_model=VisionResponse)
async def analyze_scene(
    file: UploadFile = File(...),
    query: str = Form("Describe my surroundings."),
    senior_mode: str = Form("false"),
    language: str = Form("en"),
):
    """Endpoint for single-frame vision analysis."""
    # Robust boolean parsing for Form data
    is_senior = senior_mode.lower() == "true"
    logger.info(
        "Received vision request: %s, query: '%s', senior: %s, lang: %s",
        file.filename,
        query,
        is_senior,
        language,
    )

    if not file.content_type.startswith("image/"):
        logger.warning("Invalid content type for vision: %s", file.content_type)
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        contents = await file.read()

        result = await RUNTIME.analyze_scene(
            image_data=contents,
            query=query,
            senior_mode=is_senior,
            language=language,
        )
        result_vision = result.get("vision", {})
        logger.info(
            "Final Vision feedback: %s | %s",
            result_vision.get("scene"),
            result_vision.get("guidance"),
        )
        return result_vision

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error in vision analysis: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/analyze_audio", response_model=AudioResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    query: str = Form("Describe the environment audio."),
    senior_mode: str = Form("false"),
    language: str = Form("en"),
):
    """Endpoint for short audio snippet analysis."""
    is_senior = senior_mode.lower() == "true"
    logger.info(
        "Received audio request: %s, type: %s, query: '%s', senior: %s, lang: %s",
        file.filename,
        file.content_type,
        query,
        is_senior,
        language,
    )

    try:
        audio_bytes = await file.read()

        result = await RUNTIME.analyze_scene(
            audio_data=audio_bytes,
            mime_type=file.content_type,
            query=query,
            senior_mode=is_senior,
            language=language,
        )
        logger.info("Agent audio analysis complete.")
        return result["audio"]

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error in audio analysis: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/navigate", response_model=NavigationResponse)
async def navigate(
    current_status: str = Form(...),
    destination: Optional[str] = Form(None),
    senior_mode: str = Form("false"),
    language: str = Form("en"),
):
    """Endpoint for navigation guidance."""
    is_senior = senior_mode.lower() == "true"
    logger.info(
        "Navigation request: status='%s', dest='%s', senior=%s",
        current_status,
        destination,
        is_senior,
    )

    try:
        result = await RUNTIME.navigation_agent.analyze(
            data=current_status,
            destination=destination,
            senior_mode=is_senior,
            language=language,
            session_service=RUNTIME.session_service,
            session_id=RUNTIME.session_id,
        )
        return result
    except Exception as e:
        logger.error("Error in navigation: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time Multimodal Live stream."""
    await websocket.accept()
    logger.info("New WebSocket connection for live accessibility stream.")

    # Configuration from client passed via query params
    senior_mode = websocket.query_params.get("senior_mode", "false").lower() == "true"
    language = websocket.query_params.get("language", "en")

    logger.info("Live WebSocket started. Senior: %s, Lang: %s", senior_mode, language)

    try:
        # 1. Start Gemini Live Session via VisionAgent
        async with await RUNTIME.vision_agent.start_live_session(
            context_agent=RUNTIME.context_agent,
            senior_mode=senior_mode,
            language=language,
        ) as session:
            logger.info("Gemini Live Session connected via VisionAgent.")

            async def send_to_gemini():
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        if not data:
                            continue

                        msg_type = data[0]
                        payload = data[1:]

                        if msg_type == 0x01:
                            await session.send_realtime_input(
                                media_chunks=[
                                    genai_types.Blob(
                                        data=payload, mime_type="image/jpeg"
                                    )
                                ]
                            )
                        elif msg_type == 0x02:
                            await session.send_realtime_input(
                                media_chunks=[
                                    genai_types.Blob(
                                        data=payload, mime_type="audio/webm"
                                    )
                                ]
                            )
                except WebSocketDisconnect:
                    logger.info("Frontend WebSocket disconnected.")
                    raise
                except Exception as e:  # pylint: disable=broad-except
                    logger.error("Error sending to Gemini: %s", e)

            async def receive_from_gemini():
                try:
                    async for response in session.receive():
                        if (
                            response.server_content
                            and response.server_content.model_turn
                        ):
                            for part in response.server_content.model_turn.parts:
                                if part.inline_data:
                                    await websocket.send_bytes(part.inline_data.data)
                except Exception as e:  # pylint: disable=broad-except
                    logger.error("Error receiving from Gemini: %s", e)

            # Run both tasks concurrently
            await asyncio.gather(send_to_gemini(), receive_from_gemini())

    except WebSocketDisconnect:
        logger.info("Live WebSocket session ended.")
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Fatal error in live WebSocket: %s", e)
    finally:
        logger.info("Cleaning up Live WebSocket session.")
