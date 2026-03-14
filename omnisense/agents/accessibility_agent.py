"""
Accessibility Agent - Base class for all sensory agents in OmniSense.
"""

import json
import logging
import os
import uuid
from abc import ABC, abstractmethod

from dotenv import load_dotenv
import google.genai as genai
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, GenerateContentConfig, Part

# Point to central config - checking config/ directory as primary source
_base_dir = os.path.dirname(__file__)
config_path = os.path.abspath(os.path.join(_base_dir, "..", "config", ".env"))
if not os.path.exists(config_path):
    # Fallback to local omnisense root if running nested
    config_path = os.path.abspath(os.path.join(_base_dir, "..", ".env"))
load_dotenv(config_path, override=True)


logger = logging.getLogger("omnisense-agent")


class AccessibilityAgent(ABC):
    """
    Base abstract class for agents providing sensory accessibility.
    """

    def __init__(self, name, description, model_id=None, instruction=None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # Ensure a valid model ID fallback - now exclusively from env or provided
        self.model_id = model_id or os.getenv("GEMINI_MODEL_ID")
        self.agent_name = name
        self.description = description

        # Load metadata from JSON Agent Card if available
        self.metadata = {}
        card_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "cards", f"{name}_Card.json")
        )
        if os.path.exists(card_path):
            try:
                with open(card_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info("[%s] Loaded metadata from %s", name, card_path)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("[%s] Could not load Agent Card: %s", name, e)

        # Use metadata mission/description if available
        final_description = self.metadata.get("description", description)
        final_instruction = instruction or self.metadata.get(
            "mission", final_description
        )

        logger.info("[%s] Initializing with Model: %s", name, self.model_id)

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

            # ADK Agent definition
            self.agent = Agent(
                name=self.agent_name,
                description=final_description,
                model=self.model_id,
                instruction=final_instruction,
                generate_content_config=GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
        else:
            logger.warning("[%s] GEMINI_API_KEY NOT FOUND. Running in MOCK MODE.", name)
            self.client = None
            self.agent = None

    def get_adk_agent(self) -> Agent:
        """Returns the ADK Agent instance."""
        return self.agent

    def load_prompt(self, prompt_path):
        """Loads a prompt file with fallback path logic."""
        # Try relative to CWD
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()

        # Try relative to the agent file's directory (go up one level to root)
        alt_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", prompt_path)
        )
        if os.path.exists(alt_path):
            with open(alt_path, "r", encoding="utf-8") as f:
                return f.read()

        logger.warning(
            "[%s] Prompt not found at %s or %s",
            self.agent_name,
            prompt_path,
            alt_path,
        )
        return ""

    async def _generate_json(self, prompt, parts, schema_defaults, senior_mode=False):
        """
        Standardized method for generating and parsing JSON content from Gemini.
        Includes error handling for rate limits and busy systems.
        """
        if not self.client:
            return schema_defaults

        try:
            # Use generate_content through the client
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[prompt] + parts,
                config=GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            if not response.text:
                raise ValueError("Empty response from AI")

            data = json.loads(response.text.strip())

            # Enforce schema with defaults
            for field, default in schema_defaults.items():
                if field not in data:
                    data[field] = default
            return data

        except (ValueError, json.JSONDecodeError) as e:
            err_msg = str(e)
            logger.error("[%s] Generation error: %s", self.agent_name, err_msg)

            # Standardized Resilience: Use the same signatures as VisionAgent
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                return {
                    **schema_defaults,
                    "hazard": "System is cooling down.",
                    "guidance": "Rate limit reached. Please wait.",
                }

            if "503" in err_msg or "UNAVAILABLE" in err_msg:
                return {
                    **schema_defaults,
                    "hazard": "High demand.",
                    "guidance": "System is busy. Please try again later.",
                }

            return {**schema_defaults, "guidance": f"System error: {err_msg}"}

    async def run_adk(
        self,
        user_message=None,
        schema_defaults=None,
        app_name="OmniSense",
        user_id="omnisense_user",
        custom_instruction=None,
        session_service=None,
        session_id=None,
    ):
        """
        Unified ADK Runner implementation for all sensory agents.
        Handles A2A session management, event-driven execution, and resilience.
        """
        schema_defaults = schema_defaults or {}

        if not self.agent:
            logger.warning("[%s] run_adk called in MOCK MODE.", self.agent_name)
            return {
                **schema_defaults,
                "guidance": "Running in mock mode. No AI connectivity.",
            }

        try:
            # Use current agent definition or a localized clone
            run_agent = self.agent
            if custom_instruction:
                run_agent = self.agent.model_copy(
                    update={
                        "instruction": custom_instruction,
                        "generate_content_config": GenerateContentConfig(
                            response_mime_type="application/json"
                        ),
                    }
                )
            elif not getattr(
                run_agent.generate_content_config, "response_mime_type", None
            ):
                run_agent = self.agent.model_copy(
                    update={
                        "generate_content_config": GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    }
                )

            # ADK Session Management - Use provided service or create local one
            if session_service is None:
                session_service = InMemorySessionService()

            if session_id is None:
                session_id = str(uuid.uuid4())

            # Execute via ADK Runner with auto-session creation
            runner = Runner(
                agent=run_agent,
                app_name=app_name,
                session_service=session_service,
                auto_create_session=True,
            )

            final_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
            ):
                if getattr(event, "content", None) and event.content.parts:
                    final_text += "".join(p.text for p in event.content.parts if p.text)

            if not final_text:
                error_msg = getattr(
                    event, "error_message", "AI response was empty or blocked."
                )
                raise ValueError(error_msg)

            # Parse JSON with resilience
            if "```json" in final_text:
                final_text = final_text.split("```json")[1].split("```")[0]
            elif "```" in final_text:
                final_text = final_text.split("```")[1].split("```")[0]

            data = json.loads(final_text.strip())

            # Schema Enforcement
            for field, default in schema_defaults.items():
                if field not in data:
                    data[field] = default
            return data

        except (ValueError, json.JSONDecodeError) as e:
            err_msg = str(e)
            logger.error("[%s] ADK Execution error: %s", self.agent_name, err_msg)

            # Standardized Resilience for common Gemini/ADK errors
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                return {
                    **schema_defaults,
                    "guidance": "Rate limit reached. Please wait.",
                }
            if "503" in err_msg or "UNAVAILABLE" in err_msg:
                return {
                    **schema_defaults,
                    "guidance": "System is busy. Please try again later.",
                }

            return {**schema_defaults, "guidance": f"System error: {err_msg}"}

    @abstractmethod
    async def analyze(self, data, **kwargs) -> dict:
        """
        Perform analysis on the provided data.

        Args:
            data: The input sensory data (image/audio bytes).
            **kwargs: Extra parameters for analysis (senior_mode, language, etc).
        """
        return {}
