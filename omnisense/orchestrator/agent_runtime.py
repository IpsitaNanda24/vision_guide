"""
Agent Runtime - Orchestrator for managing and coordinating multiple sensory agents.
"""

import logging

from google.adk.sessions import InMemorySessionService

from agents.audio_agent import AudioAgent
from agents.context_agent import ContextAgent
from agents.navigation_agent import NavigationAgent
from agents.vision_agent import VisionAgent

logger = logging.getLogger("omnisense-runtime")


class AgentRuntime:
    """
    Main orchestrator for managing sensory agents and their shared state.
    """

    def __init__(self):
        self.vision_agent = VisionAgent()
        self.audio_agent = AudioAgent()
        self.context_agent = ContextAgent()
        self.navigation_agent = NavigationAgent()

        # Centralized ADK Session Management for Cross-Sensory Memory
        self.session_service = InMemorySessionService()
        # Primary session for memory persistence
        self.session_id = "omnisense_static_session"

        logger.info("AgentRuntime and 3 ADK runners initialized.")

    async def initialize_sessions(self):
        """Pre-creates the shared session to avoid race conditions."""
        await self.session_service.create_session(
            app_name="OmniSense",
            user_id="omnisense_user",
            session_id=self.session_id,
        )
        logger.info(
            "Persistent session '%s' initialized for 'omnisense_user'.",
            self.session_id,
        )

    async def analyze_scene(
        self,
        image_data=None,
        audio_data=None,
        mime_type="audio/webm",
        query="Describe my surroundings.",
        senior_mode=False,
        language="en",
    ):
        results = {}

        if image_data:
            # Pass the global session_service and stable session_id
            vision_result = await self.vision_agent.analyze(
                image_data,
                context_agent=self.context_agent,
                query=query,
                senior_mode=senior_mode,
                language=language,
                session_service=self.session_service,
                session_id=self.session_id,
            )

            # Update memory service
            context_result = await self.context_agent.analyze(vision_result)

            # Post-process with historical insights
            if context_result.get("is_persistent_hazard"):
                vision_result["hazard"] = f"[PERSISTENT] {vision_result['hazard']}"
                vision_result["guidance"] = f"Stay alert! {vision_result['guidance']}"

            results["vision"] = vision_result

        if audio_data:
            audio_result = await self.analyze_audio(
                audio_data,
                mime_type=mime_type,
                query=query,
                senior_mode=senior_mode,
                language=language,
            )
            results["audio"] = audio_result

        return results

    async def analyze_audio(
        self,
        audio_data,
        mime_type="audio/webm",
        query="Describe the environment audio.",
        senior_mode=False,
        language="en",
    ):
        # Pass the global session_service and stable session_id
        audio_result = await self.audio_agent.analyze(
            audio_data,
            mime_type=mime_type,
            context_agent=self.context_agent,
            query=query,
            senior_mode=senior_mode,
            language=language,
            session_service=self.session_service,
            session_id=self.session_id,
        )
        # Update memory with audio events
        await self.context_agent.analyze(
            {
                "scene": "Audio event",
                "hazard": audio_result.get("sound_event"),
                "guidance": audio_result.get("guidance"),
            }
        )
        return audio_result

    def get_adk_agents(self):
        """Returns a list of all ADK agents managed by this runtime."""
        return [
            self.vision_agent.get_adk_agent(),
            self.audio_agent.get_adk_agent(),
            self.context_agent.get_adk_agent(),
            self.navigation_agent.get_adk_agent(),
        ]
