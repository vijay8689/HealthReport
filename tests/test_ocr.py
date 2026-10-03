import pytest

from healthlens.ingestion import IntakeError, tesseract_command


def test_configured_tesseract_path(monkeypatch, tmp_path):
    executable = tmp_path / "tesseract.exe"
    executable.write_bytes(b"test")
    monkeypatch.setenv("TESSERACT_CMD", str(executable))
    assert tesseract_command() == str(executable)


def test_timeout_reports_timeout_instead_of_missing_installation(monkeypatch):
    import pytesseract
    from PIL import Image
    from healthlens.ingestion import ocr_image
    monkeypatch.setattr("healthlens.ingestion.tesseract_command", lambda: "tesseract")
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 60
        raise RuntimeError("Tesseract process timeout")
    monkeypatch.setattr(pytesseract, "image_to_string", timeout)
    with pytest.raises(IntakeError, match="timed out"):
        ocr_image(Image.new("RGB", (20, 20)))


def test_engine_error_retains_diagnostic(monkeypatch):
    import pytesseract
    from PIL import Image
    from healthlens.ingestion import ocr_image
    monkeypatch.setattr("healthlens.ingestion.tesseract_command", lambda: "tesseract")
    def failure(*args, **kwargs):
        raise pytesseract.TesseractError(1, "Failed loading language eng")
    monkeypatch.setattr(pytesseract, "image_to_string", failure)
    with pytest.raises(IntakeError, match="Failed loading language eng"):
        ocr_image(Image.new("RGB", (20, 20)))


def test_bad_custom_path_has_actionable_error(monkeypatch):
    monkeypatch.setenv("TESSERACT_CMD", "missing-tesseract.exe")
    with pytest.raises(IntakeError, match="configured path"):
        tesseract_command()


def test_path_discovery(monkeypatch):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr("healthlens.ingestion.shutil.which", lambda name: "installed/tesseract")
    assert tesseract_command() == "installed/tesseract"


def test_windows_install_discovery_without_path(monkeypatch, tmp_path):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr("healthlens.ingestion.shutil.which", lambda name: None)
    monkeypatch.setattr("healthlens.ingestion.os.name", "nt")
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    executable = tmp_path / "Tesseract-OCR" / "tesseract.exe"
    executable.parent.mkdir()
    executable.write_bytes(b"test")
    assert tesseract_command() == str(executable)
