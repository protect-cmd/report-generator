import pytest
from utils.prompt_loader import load_prompt, STATE_MAP, NOTICE_TYPE_MAP


FORM_DATA = {
    "full_name": "John Smith",
    "property_address": "123 Main St",
    "city": "Atlanta",
    "state": "Georgia",
    "county": "Fulton",
    "tenant_full_legal_name": "Jane Doe",
    "additional_tenants": None,
    "lease_start_date": "2023-01-01",
    "monthly_rent": "1500",
    "total_amount_owed": "3000",
    "date_rent_last_paid": "2024-10-01",
    "months_unpaid": "2",
}


def test_state_map_contains_all_states():
    expected = {"Georgia", "Texas", "South Carolina", "Tennessee", "Indiana"}
    assert expected == set(STATE_MAP.keys())


def test_notice_type_map_contains_all_keys():
    expected = {"3-Day Pay or Quit", "30-Day Notice", "60-Day Notice", "Full UD Package"}
    assert expected == set(NOTICE_TYPE_MAP.keys())


def test_load_prompt_returns_string_with_variables_injected(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "georgia_3day.txt").write_text(
        "Tenant: {{tenant_full_legal_name}}\nRent: ${{monthly_rent}}"
    )

    result = load_prompt("Georgia", "3-Day Pay or Quit", FORM_DATA, prompts_dir=prompt_dir)

    assert "Jane Doe" in result
    assert "1500" in result
    assert "{{" not in result


def test_load_prompt_replaces_none_with_na(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "georgia_3day.txt").write_text("Extra: {{additional_tenants}}")

    result = load_prompt("Georgia", "3-Day Pay or Quit", FORM_DATA, prompts_dir=prompt_dir)

    assert "N/A" in result


def test_load_prompt_replaces_empty_string_with_na(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "georgia_3day.txt").write_text("Phone: {{tenant_phone}}")

    data = {**FORM_DATA, "tenant_phone": ""}
    result = load_prompt("Georgia", "3-Day Pay or Quit", data, prompts_dir=prompt_dir)

    assert "N/A" in result


def test_load_prompt_injects_date_of_notice(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "georgia_3day.txt").write_text("Date: {{date_of_notice}}")

    result = load_prompt("Georgia", "3-Day Pay or Quit", FORM_DATA, prompts_dir=prompt_dir)

    assert "{{" not in result
    assert "N/A" not in result  # date_of_notice should always have a real value


def test_load_prompt_raises_for_unknown_state():
    with pytest.raises(ValueError, match="No prompt found"):
        load_prompt("Montana", "3-Day Pay or Quit", FORM_DATA)


def test_load_prompt_raises_for_unknown_notice_type():
    with pytest.raises(ValueError, match="No prompt found"):
        load_prompt("Georgia", "Unknown Notice", FORM_DATA)


def test_30_day_and_60_day_map_to_same_file(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "georgia_3060day.txt").write_text("Content")

    result_30 = load_prompt("Georgia", "30-Day Notice", FORM_DATA, prompts_dir=prompt_dir)
    result_60 = load_prompt("Georgia", "60-Day Notice", FORM_DATA, prompts_dir=prompt_dir)

    assert result_30 == result_60


def test_zero_value_is_not_replaced_with_na(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "georgia_3day.txt").write_text("Owed: ${{total_amount_owed}}\nMonths: {{months_unpaid}}")

    data = {**FORM_DATA, "total_amount_owed": 0, "months_unpaid": 0}
    result = load_prompt("Georgia", "3-Day Pay or Quit", data, prompts_dir=prompt_dir)

    assert "$0" in result
    assert "Months: 0" in result
    assert "N/A" not in result


def test_missing_prompt_file_raises_value_error(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    # No file created — should raise ValueError not FileNotFoundError

    with pytest.raises(ValueError, match="No prompt file found"):
        load_prompt("Georgia", "3-Day Pay or Quit", FORM_DATA, prompts_dir=prompt_dir)
