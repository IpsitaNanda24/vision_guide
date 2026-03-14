import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


async def test_audio():
    try:
        from orchestrator.agent_runtime import AgentRuntime

        runtime = AgentRuntime()
        await runtime.initialize_sessions()

        dummy_data = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        print("Testing AgentRuntime.analyze_audio...")

        result = await runtime.analyze_audio(dummy_data, query="Is there any siren in the distance?")
        print("\nResult:")
        import json

        print(json.dumps(result, indent=2))

        if (
            result.get("sound_event")
            and "unknown" not in result.get("sound_event").lower()
        ):
            print("\nSUCCESS: Audio analysis returned a valid result.")
        else:
            print("\nFAILURE: Audio analysis returned unknown or error.")
    except Exception as e:
        print("\nCaught Exception in Test Script:", e)


if __name__ == "__main__":
    asyncio.run(test_audio())
