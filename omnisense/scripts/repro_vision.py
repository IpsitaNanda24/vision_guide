import asyncio
import io
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("PIL not found. Please install pillow.")
    sys.exit(1)

# Add omnisense to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "omnisense")))


async def test_vision():
    try:
        from orchestrator.agent_runtime import AgentRuntime

        runtime = AgentRuntime()
        await runtime.initialize_sessions()

        # Create a dummy image
        img = Image.new("RGB", (100, 100), color=(73, 109, 137))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_data = img_byte_arr.getvalue()

        query = "What color is the image?"
        print(f"Testing vision with query: '{query}'")

        result = await runtime.analyze_scene(
            image_data=img_data, query=query, senior_mode=False, language="en"
        )

        print("\nResponse:")
        import json

        print(json.dumps(result, indent=2))

        vision_result = result.get("vision", {})
        scene = vision_result.get("scene", "").lower()
        if (
            "color" in scene or "blue" in scene or "grey" in scene
        ):  # It's a slate blue color
            print("\nSUCCESS: Found answer in response.")
        else:
            print("\nFAILURE: Answer not found in 'scene' field.")

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_vision())
