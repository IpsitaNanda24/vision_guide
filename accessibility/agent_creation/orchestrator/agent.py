import logging
import sys
import os

from config.secrets import load_secrets
load_secrets()

from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Ensure parent directory is in the path to import sibling agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_agent.agent import VideoAgent
from audio_agent.agent import AudioAgent
from context_agent.agent import ContextAgent

logger = logging.getLogger("omnisense-orchestrator")

ORCHESTRATOR_INSTRUCTION = """You are the OmniSense Orchestrator, a high-level accessibility assistant.
Your goal is to coordinate the OmniSense subsystem agents (VideoAgent, AudioAgent, and ContextAgent) 
to provide a seamless, rich, and proactive environmental description to visually challenged users.

You have access to the following A2A sub-agents:
- VideoAgent: Use this agent to analyze images or video frames and identify spatial scenes, hazards, and navigation guidance.
- AudioAgent: Use this agent to analyze audio data for important environmental sounds, sirens, and voices.
- ContextAgent: Use this agent to query historical environmental memory, past hazards, and recent context.

When a user asks a question about their surroundings, you should evaluate which agents need to be queried, collect their A2A outputs, and synthesise a comprehensive answer. Provide proactive guidance if hazards are identified.
"""

class OrchestratorAgent:
    """
    Orchestrates OmniSense Vision, Audio, and Context agents.
    Provides a unified A2A interface and delegates tasks via ADK sub-agent routing.
    """
    def __init__(self):
        # Initialize the underlying agents
        self.video_agent_instance = VideoAgent()
        self.audio_agent_instance = AudioAgent()
        self.context_agent_instance = ContextAgent()

        # ADK standard Orchestrator Agent with A2A sub-agents
        self.agent = Agent(
            model="gemini-2.5-flash",
            name="OmniSenseOrchestrator",
            description=(
                "Main coordinating agent for the OmniSense accessibility platform. "
                "Routes tasks to Vision, Audio, and Context agents via A2A protocol."
            ),
            instruction=ORCHESTRATOR_INSTRUCTION,
            sub_agents=[
                self.video_agent_instance.agent,
                self.audio_agent_instance.agent,
                self.context_agent_instance.agent
            ]
        )

    async def run(self, message: str, image_data: bytes = None, audio_data: bytes = None) -> str:
        """
        Runs the orchestrator to coordinate a response across sub-agents based on the user's message.
        """
        runner = Runner(agent=self.agent, session_service=InMemorySessionService())

        parts = [types.Part.from_text(text=message)]
        if image_data:
            parts.append(types.Part.from_bytes(data=image_data, mime_type="image/jpeg"))
        if audio_data:
            parts.append(types.Part.from_bytes(data=audio_data, mime_type="audio/webm"))

        user_content = types.Content(role="user", parts=parts)
        
        response_text = ""
        try:
            async for chunk in runner.run_async(user_content):
                if hasattr(chunk, 'text') and chunk.text:
                    response_text += chunk.text
        except Exception as e:
            logger.error(f"Orchestrator execution failed: {e}")
            return "System Error: The Orchestrator encountered an issue processing your request."

        return response_text.strip()

# ADK-compatible module-level root_agent
root_agent = OrchestratorAgent().agent
