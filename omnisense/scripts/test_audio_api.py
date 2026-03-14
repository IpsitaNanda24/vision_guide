import requests


def test_audio_api():
    url = "http://localhost:8000/analyze_audio"

    # Create a dummy small wav file data
    dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"

    files = {"file": ("audio.webm", dummy_wav, "audio/webm")}
    data = {"senior_mode": "false", "language": "en"}

    print(f"Sending POST request to {url}...")
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.json())

        if response.status_code == 200:
            print("\nSUCCESS: API responded correctly.")
        else:
            print("\nFAILURE: API returned error status.")

    except Exception as e:
        print(f"\nError occurred: {e}")


if __name__ == "__main__":
    test_audio_api()
