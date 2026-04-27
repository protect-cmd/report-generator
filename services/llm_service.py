import json
import os
import re

from openai import OpenAI


def generate_document(populated_prompt: str) -> dict:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": populated_prompt}],
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if the model wrapped the JSON
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\n\nRaw output:\n{raw[:500]}")
