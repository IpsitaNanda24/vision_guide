"""
Audio Agent - Environmental sound detection and description.
"""

import logging
import os

from google.genai.types import Content, GenerateContentConfig, LiveConnectConfig, Modality, Part

from agents.accessibility_agent import AccessibilityAgent

logger = logging.getLogger("omnisense-audio")


class AudioAgent(AccessibilityAgent):
    """
    Agent for detecting and alerting on environmental sound events.
    """

    def __init__(self):
        description = (
            "Environmental sound detection for deaf and hard-of-hearing users. "
            "Identifies sirens, doorbells, bicycle bells, approaching vehicles, "
            "and distant voices, providing urgency-rated alerts."
        )
        self.agent_name = "AudioAgent"
        self.system_prompt = self.load_prompt("prompts/audio_prompt.txt")

        # Reference-specific instruction extension
        base_inst = self.system_prompt if self.system_prompt else description
        adk_instruction = (
            base_inst
            + """
In live sessions, detect significant environmental sounds and describe
them clearly in the transcript using brackets.
"""
        )

        # Support separate Live model for Native Audio Preview
        live_model = os.getenv("GEMINI_MODEL_LIVE_ID")
        self.live_model_id = live_model if live_model else None

        super().__init__(
            name="AudioAgent",
            description=description,
            model_id=os.getenv("GEMINI_MODEL_ID"),
            instruction=adk_instruction,
        )

    def _build_contextual_prompt(
        self,
        context_agent=None,
        query=None,
        senior_mode=False,
        language="en",
        is_live=False,
    ):
        """
        Helper method to construct the system instructions.
        Centralizes the logic for Senior Mode, Language, and Memory.
        """
        # A2A: Retrieve historical context
        context_string = "First observation."
        if context_agent:
            context_string = context_agent.get_context_for_prompt()

        if is_live:
            prompt = (
                "You are a real-time audio accessibility assistant. "
                "Listen to the environment and describe significant sounds."
            )
        else:
            prompt = (
                self.system_prompt
                if self.system_prompt
                else (
                    "Describe important sounds in this audio for a deaf or "
                    "hard-of-hearing person."
                )
            )

        # Add Senior Citizen / Social instructions
        if senior_mode:
            logger.info(
                "[%s] SENIOR CITIZEN MODE ACTIVE for audio analysis.",
                self.agent_name,
            )
            prompt += (
                "\n\nSENIOR CITIZEN MODE ACTIVE: You are a warm, patient, "
                "and intellectually engaging companion. Please include:\n"
                "1. Small talk or a positive quote to brighten their day.\n"
                "2. Reminders for healthy habits: hydration, eating healthy, "
                "or light exercise.\n"
                "3. A gentle check about their medication if it's high time.\n"
                "4. If you hear voices or interesting sounds, engage in small "
                "talk or share an intellectual observation about the sound "
                "landscape.\nKeep your tone encouraging and friendly."
            )

        # Add Language instructions
        if language != "en":
            lang_map = {"fr": "French", "hi": "Hindi", "or": "Odia"}
            target_lang = lang_map.get(language, "English")
            prompt += (
                f"\n\nLANGUAGE REQUIREMENT: Respond in {target_lang}. "
                "Ensure all text fields in the output JSON (sound_event, urgency, "
                f"guidance) are in {target_lang}."
            )

        if context_string and context_string != "First observation.":
            prompt = f"Context from previous observation: {context_string}\n\n{prompt}"

        if not is_live and query:
            prompt += f"\n\nUser's specific request: {query}"

        return prompt

    async def analyze(
        self,
        data,
        mime_type=None,
        context_agent=None,
        query="Describe the environment audio.",
        senior_mode=False,
        language="en",
        session_service=None,
        session_id=None,
        **kwargs,
    ):
        """
        Analyzes audio data with support for Senior Citizen Mode,
        multiple languages, and context-awareness via ADK.
        """
        audio_data = data
        schema_defaults = {
            "sound_event": "Sound event unknown.",
            "urgency": "Normal",
            "guidance": "No guidance provided for this sound.",
        }

        if not self.agent:
            return {
                "sound_event": "Mock: Distant siren detected.",
                "urgency": "Caution",
                "guidance": "I hear a siren in the distance. Please stay on "
                "the sidewalk and be aware of emergency vehicles.",
            }

        if not mime_type or mime_type in ["application/octet-stream", ""]:
            mime_type = "audio/webm"

        clean_mime_type = mime_type.split(";")[0].strip()

        # Build standardized prompt with context
        prompt = self._build_contextual_prompt(
            context_agent=context_agent,
            query=query,
            senior_mode=senior_mode,
            language=language,
        )

        # Wrap audio data explicitly for ADK
        # Including a text part is crucial for Multimodal attention
        user_message = Content(
            role="user",
            parts=[
                Part.from_bytes(data=audio_data, mime_type=clean_mime_type),
                Part.from_text(text=f"User query: {query}"),
            ],
        )

        # Execute via unified ADK Runner
        return await self.run_adk(
            user_message=user_message,
            schema_defaults=schema_defaults,
            custom_instruction=prompt,
            session_service=session_service,
            session_id=session_id,
        )

    async def start_live_session(
        self, context_agent=None, senior_mode=False, language="en"
    ):
        """
        Initiates a real-time WebSocket connection for audio analysis.
        """
        if not self.client:
            raise ValueError("Gemini client not initialized.")

        system_instruction = self._build_contextual_prompt(
            context_agent=context_agent,
            senior_mode=senior_mode,
            language=language,
            is_live=True,
        )

        session_model = self.live_model_id or self.model_id

        config = LiveConnectConfig(
            response_modalities=[Modality.AUDIO],
            system_instruction=Content(
                parts=[Part.from_text(text=system_instruction)]
            ),
        )

        logger.info("Starting Live Audio Session with model: %s", session_model)
        return self.client.aio.live.connect(model=session_model, config=config)
