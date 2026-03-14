import asyncio
import os

from dotenv import load_dotenv

from orchestrator.agent_runtime import AgentRuntime


async def test_navigation():
    load_dotenv()
    print("Initializing AgentRuntime...")
    runtime = AgentRuntime()
    await runtime.initialize_sessions()

    print("\nTesting NavigationAgent...")
    status = "I am at the entrance of a park. I see a paved path ahead."
    destination = "The public restroom near the fountain."

    result = await runtime.navigation_agent.analyze(
        data=status,
        destination=destination,
        session_service=runtime.session_service,
        session_id=runtime.session_id,
    )

    print(f"Status: {status}")
    print(f"Destination: {destination}")
    print("\nAgent Guidance:")
    print(f"Direction: {result.get('direction')}")
    print(f"Landmark: {result.get('landmark')}")
    print(f"Caution: {result.get('caution')}")
    print(f"Progress: {result.get('progress')}")


if __name__ == "__main__":
    asyncio.run(test_navigation())
