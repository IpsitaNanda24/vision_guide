import logging
import os

from google.genai.types import Content, GenerateContentConfig, LiveConnectConfig, Modality, Part

from agents.accessibility_agent import AccessibilityAgent

logger = logging.getLogger("omnisense-vision")


class VisionAgent(AccessibilityAgent):
    def __init__(self):
        description = (
            "Real-time camera frame analysis. Identifies scenes, obstacles, "
            "hazards, and navigation cues for visually impaired users using "
            "spatial language."
        )
        self.agent_name = "VisionAgent"
        self.static_prompt = self.load_prompt("prompts/vision_prompt.txt")
        self.live_prompt = self.load_prompt("prompts/live_vision_prompt.txt")

        # Reference-specific instruction extension
        base_inst = self.static_prompt if self.static_prompt else description
        adk_instruction = (
            base_inst
            + """
For continuous live sessions, your goal is to be a calm, caring navigation
companion. Report scene changes, hazards, and guidance in clear speech.
"""
        )

        # Support separate Live model for Native Audio Preview
        live_model = os.getenv("GEMINI_MODEL_LIVE_ID")
        self.live_model_id = live_model if live_model else None

        AccessibilityAgent.__init__(
            self,
            "VisionAgent",
            description,
            os.getenv("GEMINI_MODEL_ID"),
            adk_instruction,
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

        # Handle the base prompt
        if is_live:
            prompt = (
                self.live_prompt
                if self.live_prompt
                else (
                    "You are a real-time vision assistant. "
                    "Analyze the video and audio stream."
                )
            )
        else:
            if self.static_prompt:
                prompt = self.static_prompt.replace("{{USER_QUERY}}", query)
            else:
                prompt = f"Analyze this image. User query: {query}"

        # Add Senior Citizen / Social instructions
        if senior_mode:
            logger.info("[%s] SENIOR CITIZEN MODE ACTIVE.", self.agent_name)
            prompt += (
                "\n\nSENIOR CITIZEN MODE ACTIVE: You are a warm, patient, "
                "and intellectually engaging companion. Please include:\n"
                "1. Small talk or a positive quote to brighten their day.\n"
                "2. Reminders for healthy habits: hydration, eating healthy, "
                "or light exercise.\n"
                "3. A gentle check about their medication if it's high time.\n"
                "4. Intellectual conversation about the visual scene "
                "(share historical facts or interesting observations).\n"
                "Keep your tone encouraging and friendly."
            )

        # Add Language instructions
        if language != "en":
            lang_map = {"fr": "French", "hi": "Hindi", "or": "Odia"}
            target_lang = lang_map.get(language, "English")
            if is_live:
                prompt += (
                    f"\n\nLANGUAGE REQUIREMENT: You must speak and "
                    f"respond exclusively in {target_lang}."
                )
            else:
                prompt += (
                    f"\n\nLANGUAGE REQUIREMENT: Respond in {target_lang}. "
                    "Ensure all text fields in the output JSON (scene, hazard, "
                    f"guidance) are in {target_lang}."
                )

        if context_string and context_string != "First observation.":
            prompt = f"Context from previous observation: {context_string}\n\n{prompt}"

        # IMPORTANT: Ensure the specific user query is prioritized
        if not is_live and query:
            prompt += (
                f"\n\nACTUAL USER QUESTION: {query}\n"
                "Please answer this question directly in the 'scene' field "
                "of your JSON, then continue with the rest of the environmental "
                "analysis as per your system instructions."
            )

        return prompt

    # ==========================================
    # 1. PRESERVED: Single-shot JSON Analysis
    # ==========================================
    async def analyze(
        self,
        data,
        context_agent=None,
        query="Describe my surroundings.",
        senior_mode=False,
        language="en",
        session_service=None,
        session_id=None,
        **kwargs,
    ):
        """
        Analyzes a single image and returns a structured JSON dictionary.
        """
        image_data = data
        if not self.client:
            return {
                "scene": "Mock: A bright, modern hallway.",
                "hazard": "Mock: None detected.",
                "guidance": "AI model not configured.",
                "safety_level": "Safe",
            }

        prompt = self._build_contextual_prompt(
            context_agent, query, senior_mode, language, is_live=False
        )
        schema_defaults = {
            "scene": "Scene description unavailable.",
            "hazard": "No hazard information.",
            "guidance": "No guidance provided.",
            "safety_level": "Unknown",
        }

        # Wrap image data explicitly for ADK.
        # Including query in message parts ensures much higher attention.
        user_message = Content(
            role="user",
            parts=[
                Part.from_bytes(data=image_data, mime_type="image/jpeg"),
                Part.from_text(text=f"User's specific question: {query}"),
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

    # ==========================================
    # 2. NEW: Real-time Multimodal Live Stream
    # ==========================================
    async def start_live_session(
        self, context_agent=None, senior_mode=False, language="en"
    ):
        """
        Initiates a real-time WebSocket connection using Multimodal Live API.
        Returns active session object for sending/receiving frames.
        """
        if not self.client:
            raise ValueError("Gemini client not initialized.")

        # Build instructions for the live session
        system_instruction = self._build_contextual_prompt(
            context_agent,
            query=None,
            senior_mode=senior_mode,
            language=language,
            is_live=True,
        )

        # Use specialized live model if configured (e.g. native audio preview)
        session_model = self.live_model_id or self.model_id

        config = LiveConnectConfig(
            # Voice assistants don't return JSON, they speak!
            # Preserving types.Modality.AUDIO as requested
            response_modalities=[Modality.AUDIO],
            system_instruction=Content(
                parts=[Part.from_text(text=system_instruction)]
            ),
        )

        logger.info("Starting Live Vision Session with model: %s", session_model)

        # Return the context manager so calling function can manage stream loop
        return self.client.aio.live.connect(model=session_model, config=config)
