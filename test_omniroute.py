from openai import OpenAI
import json

client = OpenAI(
    base_url="http://localhost:20128/v1",
    api_key="sk-no-key-required"
)

try:
    print("Sending request to OmniRoute...")
    response = client.chat.completions.create(
        model='auto',
        messages=[{"role": "user", "content": "Hello, OmniRoute!"}]
    )
    print("Response received:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
