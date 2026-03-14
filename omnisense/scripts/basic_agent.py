import asyncio
import os

from dotenv import load_dotenv
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def main():
    # Load environment variables (e.g., GEMINI_API_KEY)
    load_dotenv()

    # Verify API key is present
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    print("Initializing Agent...")

    # 1. Define the ADK Agent
    # This agent uses the new genai SDK under the hood.
    agent = Agent(
        name="BasicHelper",
        description="A simple demonstrative helper agent.",
        model=os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash"),
        instruction="You are a concise, helpful assistant.",
    )

    # 2. Initialize the Session Service
    # InMemorySessionService stores chat history in memory during execution
    session_service = InMemorySessionService()

    # 3. Create the Runner
    # The runner coordinates the agent, sessions, and tools
    runner = Runner(
        agent=agent,
        app_name="BasicAdkApp",
        session_service=session_service,
        auto_create_session=True,  # Automatically create a session if it doesn't exist
    )

    user_message_text = "Hello! What is your purpose?"
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message_text)],
    )
    print(f"\nUser: {user_message_text}")
    print("Agent: ", end="", flush=True)

    # 4. Run the agent asynchronously
    # The runner yields events as the agent processes the message
    async for event in runner.run_async(
        user_id="demo_user",
        session_id="demo_session",
        new_message=user_message,
    ):
        # Extract text from the event content parts
        if getattr(event, "content", None) and event.content.parts:
            text = "".join(p.text for p in event.content.parts if p.text)
            print(text, end="", flush=True)

    print("\n\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
