import os
import sys
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def test_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "YOUR_GROQ_API_KEY":
        print("ERROR: GROQ_API_KEY is not set or is still the placeholder.")
        return

    print(f"Using API Key: {api_key[:10]}...")
    
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("SUCCESS: Groq API call worked!")
        print(f"Response: {completion.choices[0].message.content}")
    except Exception as e:
        print(f"FAILURE: Groq API call failed with error: {e}")

if __name__ == "__main__":
    test_groq()
