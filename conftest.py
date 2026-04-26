"""
Root conftest.py — stubs out WeasyPrint's native library dependencies so that
the pdf_service module can be imported in test environments where the GTK/GObject
system libraries are not available (e.g., plain Windows without MSYS2/GTK runtime).

The actual WeasyPrint HTML class is patched per-test in test_pdf_service.py, so
no real PDF rendering occurs during the test suite.
"""
import sys
from unittest.mock import MagicMock

# Only stub if weasyprint cannot be natively imported (i.e., missing native libs).
try:
    import weasyprint  # noqa: F401
except OSError:
    mock_weasyprint = MagicMock()
    mock_weasyprint.HTML = MagicMock()
    sys.modules["weasyprint"] = mock_weasyprint
