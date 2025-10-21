import os
from openai import OpenAI

# Optional: set API key here directly (if you don't want to rely on environment variable)
# os.environ["OPENAI_API_KEY"] = "your_new_api_key_here"
os.environ["OPENAI_API_KEY"] = "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"
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in a friendly way."}
    ]
)

print(response.choices[0].message.content)
