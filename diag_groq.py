import os
import sys
import traceback
from dotenv import load_dotenv
from groq import Groq

# Ensure output is UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def main():
    with open('diag_log.txt', 'w', encoding='utf-8') as f:
        try:
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
            f.write(f"API Key prefix: {api_key[:10] if api_key else 'None'}\n")
            
            if not api_key:
                f.write("ERROR: No API key found in .env\n")
                return

            f.write("Initializing Groq client...\n")
            client = Groq(api_key=api_key)
            
            # Test with two models
            models = ["llama-3.1-8b-instant", "llama3-8b-8192"]
            
            for model in models:
                f.write(f"\nTesting model: {model}\n")
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a test assistant."},
                            {"role": "user", "content": "hi"}
                        ],
                        max_tokens=10
                    )
                    f.write(f"SUCCESS: {model} worked!\n")
                    f.write(f"Response: {response.choices[0].message.content}\n")
                except Exception as e:
                    f.write(f"FAILURE for {model}: {e}\n")
                    f.write(traceback.format_exc())
                    
        except Exception as e:
            f.write(f"CRITICAL ERROR: {e}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    main()
