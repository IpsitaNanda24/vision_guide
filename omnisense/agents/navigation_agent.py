"""
Navigation Agent - Specialized in spatial guidance and route directions.
"""

import logging
import os

from google.genai import types

from agents.accessibility_agent import AccessibilityAgent

logger = logging.getLogger("omnisense-navigation")


class NavigationAgent(AccessibilityAgent):
    """
    Agent for providing turn-by-turn navigation and spatial orientation.
    """

    def __init__(self):
        description = (
            "Provides precise walking directions, landmark awareness, "
            "and spatial orientation for visually impaired users."
        )
        self.agent_name = "NavigationAgent"
        self.system_prompt = self.load_prompt("prompts/navigation_prompt.txt")

        # ADK instruction extension
        base_inst = self.system_prompt if self.system_prompt else description
        adk_instruction = (
            base_inst + "\nIn live sessions, provide frequent, small updates "
            "to keep the user centered on their path."
        )

        super().__init__(
            name="NavigationAgent",
            description=description,
            model_id=os.getenv("GEMINI_MODEL_ID"),
            instruction=adk_instruction,
        )

    def _build_contextual_prompt(
        self, destination=None, senior_mode=False, language="en"
    ):
        """
        Helper method to construct the system instructions.
        Centralizes the logic for Senior Mode, Language, and Destinations.
        """
        prompt = (
            self.system_prompt
            if self.system_prompt
            else ("Provide precise walking directions and spatial orientation.")
        )

        if destination:
            prompt += f"\n\nPRIMARY GOAL: Guide the user to {destination}."

        # Add Senior Citizen / Social instructions
        if senior_mode:
            logger.info("[%s] SENIOR CITIZEN MODE ACTIVE.", self.agent_name)
            prompt += (
                "\n\nSENIOR CITIZEN MODE ACTIVE: You are a warm, patient, "
                "and intellectually engaging companion. Please include:\n"
                "1. Small talk or a positive quote to brighten their day.\n"
                "2. Reminders for healthy habits: hydration or light exercise while walking.\n"
                "3. Encouraging words about their journey.\n"
                "Keep your tone encouraging and friendly."
            )

        # Add Language instructions
        if language != "en":
            lang_map = {"fr": "French", "hi": "Hindi", "or": "Odia"}
            target_lang = lang_map.get(language, "English")
            prompt += (
                f"\n\nLANGUAGE REQUIREMENT: Respond in {target_lang}. "
                "Ensure all text fields in the output JSON (direction, landmark, "
                f"caution) are in {target_lang}."
            )

        return prompt

    async def analyze(
        self,
        data,
        destination=None,
        senior_mode=False,
        language="en",
        session_service=None,
        session_id=None,
        **kwargs,
    ):
        """
        Calculates navigation guidance based on current location/data and destination.
        """
        schema_defaults = {
            "direction": "Proceed forward carefully.",
            "landmark": "No landmarks identified.",
            "caution": "Stay aware of your surroundings.",
            "progress": "0%",
        }

        if not self.agent:
            return {
                "direction": "Mock: Turn right in 5 meters.",
                "landmark": "Mock: You are near a park entrance.",
                "caution": "Mock: Watch for low-hanging branches.",
                "progress": "50%",
            }

        # Build standardized prompt
        prompt = self._build_contextual_prompt(
            destination=destination, senior_mode=senior_mode, language=language
        )

        # Wrap input for ADK
        user_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"Current Status: {data}")],
        )

        return await self.run_adk(
            user_message=user_message,
            schema_defaults=schema_defaults,
            custom_instruction=prompt,
            session_service=session_service,
            session_id=session_id,
        )
