import logging
import os
from typing import Dict, Any, List, Optional

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.secrets import load_secrets
load_secrets()

from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

logger = logging.getLogger("omnisense-context")

CONTEXT_INSTRUCTION = """You are the Context Agent for OmniSense. Your role is to maintain environmental memory and provide historical context to assist visually challenged users.

You work alongside:
- OmniSense Vision: provides structured snapshot analysis including "scene", "hazard", "guidance", and "safety_level".
- OmniSense Audio: provides "sound_event", "urgency", and "guidance" fields.

When given a history of observations, provide:
1. A summary of recent scenes (textures, lighting, spatial layout) to maintain a rich mental map.
2. A list of any persistent hazards identified over time (e.g., cars, low obstacles, uneven flooring).
3. A concise historical context summary that other agents can use to provide grounded, continuous navigation without repeating themselves.

Respond clearly with the current context summary and any persistent hazards to ensure the user's safety and spatial awareness are maintained.
"""

try:
    # Attempt to import generic base class from a hypothetical shared location
    from base_agent import AccessibilityAgent
except ImportError:
    # Mock base class if missing
    class AccessibilityAgent:
        def __init__(self, agent: Agent):
            self.agent = agent

class ContextAgent(AccessibilityAgent):
    """
    ADK-compliant Context Agent for OmniSense.
    Maintains environmental memory and provides A2A context to Vision and Audio agents.
    """
    def __init__(self):
        # 1. Core Agent Definition (ADK standard)
        root_agent = Agent(
            model="gemini-2.5-flash",
            name="ContextAgent",
            description=(
                "Maintains environmental memory and provides historical context "
                "via A2A to ensure navigation consistency for OmniSense agents."
            ),
            instruction=CONTEXT_INSTRUCTION,
        )
        super().__init__(root_agent)

        # 2. In-process memory (rolling window)
        self._memory: List[Dict[str, Any]] = []
        self._max_memory: int = 5
        self._persistent_hazards: List[str] = []

    # 3. Synchronous analyze — no model call needed, pure state management
    def analyze(self, new_observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates rolling memory with a new observation from Vision or Audio agent.
        Identifies persistent hazards across recent frames.
        Returns: history, context_summary, is_persistent_hazard
        """
        self._memory.append(new_observation)
        if len(self._memory) > self._max_memory:
            self._memory.pop(0)

        # Scan last 3 observations for recurring hazards
        recent = self._memory[-3:]
        hazards = [
            str(obs.get("hazard", obs.get("sound_event", ""))).lower()
            for obs in recent
            if obs.get("hazard") or obs.get("sound_event")
        ]

        # Build context summary from latest prior observation
        context_summary = "Previous context suggests: "
        if len(self._memory) > 1:
            prev = self._memory[-2]
            recent_scene = prev.get("scene", prev.get("sound_event", "Unknown"))
            context_summary += f"You were recently near: {recent_scene}."
        else:
            context_summary += "No prior context."

        is_persistent_hazard = any(
            kw in h for h in hazards for kw in ("car", "bus", "truck", "stair", "curb", "siren", "vehicle")
        )

        return {
            "history": self._memory,
            "context_summary": context_summary,
            "is_persistent_hazard": is_persistent_hazard,
        }

    # 4. A2A Service Method — returns context string for other agent prompts
    def get_context_for_prompt(self) -> str:
        """
        Returns a concise one-line context string for injection into Vision/Audio prompts.
        """
        if not self._memory:
            return "First observation — no prior context."

        recent = self._memory[-1]
        scene = recent.get("scene", recent.get("sound_event", "Unknown"))
        hazard = recent.get("hazard", recent.get("urgency", "None"))
        return f"User recently saw/heard: {scene}. Most recent hazard/alert: {hazard}."

    # 5. ADK Runner-based async query — allows external A2A calls to request context via model
    async def query(self, question: str) -> str:
        """
        Allows other agents or the orchestrator to ask the ContextAgent questions
        about the current environment via natural language (A2A pattern).
        """
        context_str = self.get_context_for_prompt()
        prompt_with_context = (
            f"Current Environment Memory:\n{context_str}\n\n"
            f"Question from orchestrator: {question}"
        )

        request_agent = self.agent.model_copy(update={"instruction": prompt_with_context})
        runner = Runner(agent=request_agent, session_service=InMemorySessionService())

        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=question)]
        )

        response_text = ""
        try:
            async for chunk in runner.run_async(user_content):
                if hasattr(chunk, "text") and chunk.text:
                    response_text += chunk.text
        except Exception as e:
            logger.error(f"ContextAgent query failed: {e}")
            return self.get_context_for_prompt()

        return response_text.strip() or self.get_context_for_prompt()

    async def get_agent_card(self) -> Dict[str, Any]:
        """
        Returns the A2A Agent Card for this agent.
        """
        builder = AgentCardBuilder(
            agent=self.agent,
            rpc_url="http://localhost:80/a2a",
            agent_version="1.0.0",
            doc_url="https://github.com/google/adk"
        )
        card = await builder.build()
        
        if hasattr(card, "model_dump"):
            return card.model_dump(exclude_none=True)
        return card.__dict__ if hasattr(card, "__dict__") else card

# ADK-compatible module-level root_agent for adk web / adk run compatibility
root_agent = ContextAgent().agent
