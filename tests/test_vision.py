from __future__ import annotations

import pytest

from brainy.vision.ocr import VisionError, extract_text_from_image


class _FakeImage:
    pass


def test_extract_text_from_image_strips_result(monkeypatch):
    monkeypatch.setattr("PIL.Image.open", lambda path: _FakeImage())
    monkeypatch.setattr("pytesseract.image_to_string", lambda image: "  hello world  \n")

    text = extract_text_from_image("fake.png")

    assert text == "hello world"


def test_extract_text_from_image_raises_on_missing_file():
    with pytest.raises(VisionError, match="could not open image"):
        extract_text_from_image("this_file_does_not_exist.png")


def test_extract_text_from_image_raises_clear_error_when_tesseract_missing(monkeypatch):
    import pytesseract

    def _raise(image):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr("PIL.Image.open", lambda path: _FakeImage())
    monkeypatch.setattr("pytesseract.image_to_string", _raise)

    with pytest.raises(VisionError, match="Tesseract OCR is not installed"):
        extract_text_from_image("fake.png")


