"""DeepSeek API client."""
import json, time, urllib.request
from config import DEEPSEEK_API_URL, DEEPSEEK_API_KEY


def call(system_prompt, user_prompt, model="deepseek-v4-pro",
         temperature=0.7, max_tokens=4096):
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_API_URL, data=payload,
        headers={
            "Authorization": "Bearer " + DEEPSEEK_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode())
                content = data["choices"][0]["message"]["content"]
                if content.strip():
                    return content
                return "[empty response - model reasoning]"
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
            if attempt == 2:
                return "ERROR after 3 retries: " + str(e)
            time.sleep(2 ** attempt)
    return "ERROR: unreachable"
