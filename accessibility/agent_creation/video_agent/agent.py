import json
import logging
import os
from typing import Dict, Any, List

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.secrets import load_secrets
load_secrets()

from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

try:
    # Attempt to import generic base class from a hypothetical shared location
    from base_agent import AccessibilityAgent
except ImportError:
    # Mock base class if missing
    class AccessibilityAgent:
        def __init__(self, agent: Agent):
            self.agent = agent

class VideoAgent(AccessibilityAgent):
    def __init__(self):
        # 1. Core Agent Definition
        root_agent = Agent(
            model='gemini-2.5-flash',
            name="VideoAgent",
            description="Real-time camera frame analysis for visually impaired users. Identifies scenes, obstacles, hazards, and navigation cues using spatial language.",
            instruction='''You are OmniSense Vision. Your mission is to provide safe navigation guidance and a rich, descriptive mental map for visually challenged users.

GROUNDING & PROACTIVITY PRINCIPLE:
- Describe ONLY what you see in the provided image/video frames.
- DO NOT make up details. However, NEVER simply refuse to give guidance.
- If you cannot see the floor or critical areas, provide "Interim Guidance":
  *   Example: "I see a clear doorway 10 feet ahead, but please tilt your camera down slightly as you walk so I can monitor for low obstacles."
  *   Example: "There seems to be an open space to your left, but I need you to pan further left for me to confirm safety."
- Always speak relative to the user's current orientation (left, right, ahead).

SPATIAL AWARENESS:
- Explain the layout in detail: "There is a sofa 5 feet to your left, a flat-screen TV on the wall ahead, and a clear path to the door on your right."
- Help the user visualize the space: mention textures and lighting.

OUTPUT FORMAT:
Respond ONLY with a JSON object:
{
  "scene": "A warm, rich description of the environment. Build a full mental map.",
  "hazard": "Specific obstacles/distances. If visibility is low, mention what you ARE looking for.",
  "guidance": "Calm, proactive step-by-step navigation instructions. Include camera adjustment advice here if needed.",
  "safety_level": "Safe", "Caution", or "Critical"
}

TONE & STYLE:
- Warm, detailed, and confident.
- Do not use word counts.
- Avoid meta-language like "I see".'''
        )
        # 2. Initialization: Register the agent with the model
        super().__init__(root_agent)

    # 3. Execution Logic
    async def analyze(self, image_data: bytes, mime_type: str = "image/jpeg", senior_mode: bool = False, language: str = "english", query: str = "Describe my surroundings.", context_summary: str = None) -> Dict[str, Any]:
        """
        Analyzes image/video frame data for spatial awareness and navigation guidance.
        """
        # 4. Contextual Logic
        dynamic_prompt = self.agent.instruction
        
        if context_summary:
            dynamic_prompt = f"Previous context suggests: {context_summary}\n\n" + dynamic_prompt

        if senior_mode:
            dynamic_prompt += (
                "\n\nSenior Mode Enabled: You are a warm, patient, and intellectually engaging companion. Please include:\n"
                "1. Small talk or a positive quote to brighten their day.\n"
                "2. Reminders for healthy habits: hydration, eating healthy, or light exercise.\n"
                "3. A gentle check about their medication if it's high time.\n"
                "4. Intellectual conversation about the visual scene (share historical facts or interesting observations).\n"
                "Keep your tone encouraging and friendly."
            )
            
        if language and language.lower() != "english":
            dynamic_prompt += f"\n\nLanguage Translation: Translate all text fields in the returned JSON object into {language}."

        dynamic_prompt += f"\n\nUser Question: {query}\nPlease answer this question directly in the 'scene' field of your JSON, then continue with the rest of the environmental analysis."

        # 2. Dynamic Context (ADK model_copy)
        request_agent = self.agent.model_copy(update={"instruction": dynamic_prompt})

        # 3. ADK Runner
        runner = Runner(agent=request_agent, session_service=InMemorySessionService())
        
        # Input Handling
        try:
            image_part = types.Part.from_bytes(data=image_data, mime_type=mime_type)
        except AttributeError:
            # Fallback for different GenAI SDK versions
            image_part = types.Part(
                inline_data=types.Blob(data=image_data, mime_type=mime_type)
            )

        user_content = types.Content(
            role="user",
            parts=[image_part]
        )
        
        # 5. Error Handling & Resilience
        try:
            # Response Processing
            response_text = ""
            async for chunk in runner.run_async(user_content):
                if hasattr(chunk, 'text') and chunk.text:
                    response_text += chunk.text
            
            # Clean up markdown backticks for JSON parsing
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:]
            
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            clean_text = clean_text.strip()
            
            result = json.loads(clean_text)
            
            # Schema defaults to ensure UI never crashes on missing fields
            return {
                "scene": result.get("scene", "Scene description unavailable."),
                "hazard": result.get("hazard", "No specific hazards identified."),
                "guidance": result.get("guidance", "No navigation guidance available."),
                "safety_level": result.get("safety_level", "Unknown")
            }
            
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON response: {response_text}")
            return {
                "scene": "Analysis Complete (Format Error)",
                "hazard": "Check surroundings carefully.",
                "guidance": "The visual analysis was completed, but the response format was invalid.",
                "safety_level": "Caution"
            }
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "resource exhausted" in error_str:
                return {
                    "scene": "System Busy",
                    "hazard": "N/A",
                    "guidance": "Our system is currently experiencing high demand. Please try again in a few moments.",
                    "safety_level": "Safe"
                }
            elif "503" in error_str or "unavailable" in error_str:
                return {
                    "scene": "System Unavailable",
                    "hazard": "N/A",
                    "guidance": "The vision analysis service is currently unavailable. Please check back later.",
                    "safety_level": "Safe"
                }
            else:
                logging.exception("Unexpected error during vision analysis")
                return {
                    "scene": "System Error",
                    "hazard": "Unknown",
                    "guidance": "An unexpected error occurred during vision analysis. Please try again.",
                    "safety_level": "Caution"
                }

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
