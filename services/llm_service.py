import os
from openai import OpenAI


def generate_document(populated_prompt: str) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": populated_prompt,
            }
        ],
    )

    return response.choices[0].message.content
