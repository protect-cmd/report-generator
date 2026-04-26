import pytest
from unittest.mock import patch, MagicMock, call
from services.pdf_service import generate_pdf


SAMPLE_TEXT = "NOTICE TO PAY OR QUIT\n\nTo: Jane Doe\nAt: 123 Main St"


def test_generate_pdf_calls_weasyprint(tmp_path):
    output_path = str(tmp_path / "test_output.pdf")

    with patch("services.pdf_service.HTML") as MockHTML:
        mock_html_instance = MagicMock()
        MockHTML.return_value = mock_html_instance

        result = generate_pdf(SAMPLE_TEXT, output_path)

        assert MockHTML.called
        mock_html_instance.write_pdf.assert_called_once_with(output_path)
        assert result == output_path


def test_generate_pdf_html_contains_document_text(tmp_path):
    output_path = str(tmp_path / "test_output.pdf")
    captured_html = {}

    def capture_html(string):
        captured_html["content"] = string
        mock = MagicMock()
        mock.write_pdf = MagicMock()
        return mock

    with patch("services.pdf_service.HTML", side_effect=capture_html):
        generate_pdf(SAMPLE_TEXT, output_path)

    assert "Jane Doe" in captured_html["content"]
    assert "123 Main St" in captured_html["content"]
    assert "font-family" in captured_html["content"]


def test_generate_pdf_html_contains_times_new_roman(tmp_path):
    output_path = str(tmp_path / "test_output.pdf")
    captured_html = {}

    def capture_html(string):
        captured_html["content"] = string
        mock = MagicMock()
        mock.write_pdf = MagicMock()
        return mock

    with patch("services.pdf_service.HTML", side_effect=capture_html):
        generate_pdf(SAMPLE_TEXT, output_path)

    assert "Times New Roman" in captured_html["content"]


def test_generate_pdf_returns_output_path(tmp_path):
    output_path = str(tmp_path / "output.pdf")
    with patch("services.pdf_service.HTML") as MockHTML:
        MockHTML.return_value.write_pdf = MagicMock()
        result = generate_pdf(SAMPLE_TEXT, output_path)
    assert result == output_path


def test_generate_pdf_converts_newlines_to_br(tmp_path):
    output_path = str(tmp_path / "output.pdf")
    captured_html = {}

    def capture_html(string):
        captured_html["content"] = string
        mock = MagicMock()
        mock.write_pdf = MagicMock()
        return mock

    text_with_newlines = "Line one\nLine two\nLine three"
    with patch("services.pdf_service.HTML", side_effect=capture_html):
        generate_pdf(text_with_newlines, output_path)

    assert "<br>" in captured_html["content"]
    assert "Line one" in captured_html["content"]
    assert "Line two" in captured_html["content"]


def test_generate_pdf_escapes_html_metacharacters(tmp_path):
    output_path = str(tmp_path / "output.pdf")
    captured_html = {}

    def capture_html(string):
        captured_html["content"] = string
        mock = MagicMock()
        mock.write_pdf = MagicMock()
        return mock

    text_with_html = 'Tenant owes $500 <see attachment> & "Exhibit A"'
    with patch("services.pdf_service.HTML", side_effect=capture_html):
        generate_pdf(text_with_html, output_path)

    assert "<see attachment>" not in captured_html["content"]
    assert "&lt;see attachment&gt;" in captured_html["content"]
    assert "&amp;" in captured_html["content"]
    assert "&quot;" in captured_html["content"]
