from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_NOTICE_KEY_TO_TEMPLATE = {
    "3day": "template_3day.html",
    "3060day": "template_3060day.html",
    "ud": "template_ud.html",
}

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def generate_pdf(document_data: dict, output_path: str, notice_key: str) -> str:
    template_name = _NOTICE_KEY_TO_TEMPLATE.get(notice_key)
    if not template_name:
        raise ValueError(f"No template for notice_key={notice_key!r}")

    template = _jinja_env.get_template(template_name)
    html = template.render(**document_data)

    from weasyprint import HTML  # noqa: PLC0415
    HTML(string=html).write_pdf(output_path)
    return output_path
