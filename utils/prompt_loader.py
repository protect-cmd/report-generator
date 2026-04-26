from datetime import date


STATE_MAP = {
    "Georgia": "georgia",
    "Texas": "texas",
    "South Carolina": "south_carolina",
    "Tennessee": "tennessee",
    "Indiana": "indiana",
}

NOTICE_TYPE_MAP = {
    "3-Day Pay or Quit": "3day",
    "30-Day Notice": "3060day",
    "60-Day Notice": "3060day",
    "Full UD Package": "ud",
}


def load_prompt(state: str, notice_type: str, form_data: dict) -> str:
    state_key = STATE_MAP.get(state)
    notice_key = NOTICE_TYPE_MAP.get(notice_type)

    if not state_key or not notice_key:
        raise ValueError(f"No prompt found for state={state}, notice_type={notice_type}")

    prompt_path = f"prompts/{state_key}_{notice_key}.txt"

    with open(prompt_path, "r") as f:
        template = f.read()

    data = {**form_data, "date_of_notice": str(date.today())}

    for key, value in data.items():
        replacement = str(value) if value else "N/A"
        template = template.replace(f"{{{{{key}}}}}", replacement)

    return template
