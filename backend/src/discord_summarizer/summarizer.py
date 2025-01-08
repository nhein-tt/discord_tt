import requests
from .config import OPENAI_API_KEY, OPENAI_API_BASE

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

def summarize_discord_data(discord_data):
    all_messages = [
        f"[{channel}] {msg['author']}: {msg['content']}"
        for channel, messages in discord_data.items()
        for msg in messages
    ]
    prompt = f"Summarize the following messages:\n\n{''.join(all_messages[:200])}"
    return call_openai_api(prompt)

def call_openai_api(prompt):
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(OPENAI_API_BASE, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
