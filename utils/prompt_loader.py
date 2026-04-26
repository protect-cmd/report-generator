from datetime import date
from pathlib import Path


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

_DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(state: str, notice_type: str, form_data: dict, prompts_dir=None) -> str:
    state_key = STATE_MAP.get(state)
    notice_key = NOTICE_TYPE_MAP.get(notice_type)

    if not state_key or not notice_key:
        raise ValueError(f"No prompt found for state={state}, notice_type={notice_type}")

    if prompts_dir is None:
        prompts_dir = _DEFAULT_PROMPTS_DIR

    prompt_path = Path(prompts_dir) / f"{state_key}_{notice_key}.txt"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        raise ValueError(f"No prompt file found at {prompt_path}")

    data = {**form_data, "date_of_notice": str(date.today())}

    for key, value in data.items():
        replacement = "N/A" if value is None or value == "" else str(value)
        template = template.replace(f"{{{{{key}}}}}", replacement)

    return template
