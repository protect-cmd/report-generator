from datetime import date
from difflib import get_close_matches
from pathlib import Path


# Canonical labels → internal keys (exact match, case-sensitive first pass)
STATE_MAP = {
    "Georgia": "georgia",
    "Texas": "texas",
    "South Carolina": "south_carolina",
    "Tennessee": "tennessee",
    "Indiana": "indiana",
    # Abbreviations
    "GA": "georgia",
    "TX": "texas",
    "SC": "south_carolina",
    "TN": "tennessee",
    "IN": "indiana",
}

NOTICE_TYPE_MAP = {
    # 3-Day variants
    "3-Day Pay or Quit": "3day",
    "3 Day Pay or Quit": "3day",
    "3-Day Notice to Pay or Quit": "3day",
    "3 Day Notice to Pay or Quit": "3day",
    "3-Day Notice": "3day",
    "3 Day Notice": "3day",
    # 30/60-Day variants
    "30-Day Notice": "3060day",
    "60-Day Notice": "3060day",
    "30 Day Notice": "3060day",
    "60 Day Notice": "3060day",
    "30/60-Day Notice to Vacate": "3060day",
    "30/60 Day Notice to Vacate": "3060day",
    "30-Day Notice to Vacate": "3060day",
    "60-Day Notice to Vacate": "3060day",
    # UD / Unlawful Detainer variants
    "Full UD Package": "ud",
    "Full Unlawful Detainer Package": "ud",
    "Unlawful Detainer Package": "ud",
    "Unlawful Detainer": "ud",
    "UD Package": "ud",
    "Full UD": "ud",
}

_DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _resolve_state(state: str) -> str | None:
    """Return the internal state key, tolerating case differences and close typos."""
    # 1. Exact match
    if state in STATE_MAP:
        return STATE_MAP[state]

    # 2. Case-insensitive match
    lower = state.strip().lower()
    for label, key in STATE_MAP.items():
        if label.lower() == lower:
            return key

    # 3. Fuzzy match (handles 1-2 character typos)
    candidates = list(STATE_MAP.keys())
    matches = get_close_matches(state, candidates, n=1, cutoff=0.7)
    if matches:
        return STATE_MAP[matches[0]]

    return None


def _resolve_notice_type(notice_type: str) -> str | None:
    """Return the internal notice key, tolerating case differences, extra words, and typos."""
    # 1. Exact match
    if notice_type in NOTICE_TYPE_MAP:
        return NOTICE_TYPE_MAP[notice_type]

    # 2. Case-insensitive exact match
    lower = notice_type.strip().lower()
    for label, key in NOTICE_TYPE_MAP.items():
        if label.lower() == lower:
            return key

    # 3. Keyword heuristics (handles novel phrasings from GHL label changes)
    tokens = lower.replace("-", " ").split()
    if any(t in tokens for t in ("ud", "detainer", "unlawful")):
        return "ud"
    if "3" in tokens and any(t in tokens for t in ("day", "pay", "quit")):
        return "3day"
    if any(t in tokens for t in ("30", "60")) and any(t in tokens for t in ("day", "notice", "vacate")):
        return "3060day"

    # 4. Fuzzy match as last resort
    candidates = list(NOTICE_TYPE_MAP.keys())
    matches = get_close_matches(notice_type, candidates, n=1, cutoff=0.5)
    if matches:
        return NOTICE_TYPE_MAP[matches[0]]

    return None


def load_prompt(state: str, notice_type: str, form_data: dict, prompts_dir=None) -> str:
    state_key = _resolve_state(state)
    notice_key = _resolve_notice_type(notice_type)

    if not state_key:
        raise ValueError(f"Unrecognised state: '{state}'. Supported: Georgia, Texas, South Carolina, Tennessee, Indiana.")
    if not notice_key:
        raise ValueError(f"Unrecognised notice type: '{notice_type}'. Expected a 3-Day, 30/60-Day, or UD variant.")

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
