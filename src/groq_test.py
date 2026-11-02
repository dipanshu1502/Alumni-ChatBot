import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL")

if not api_key or not model:
    raise ValueError("GROQ_API_KEY or GROQ_MODEL missing in .env")

# Connect to Groq
client = Groq(api_key=api_key)

# Send test request
response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Say Hello! I am testing my RAG chatbot."
        }
    ],
    temperature=0.3
)

print("\nGroq API Connected Successfully!")
print("Response:", response.choices[0].message.content)