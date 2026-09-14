from uuid import uuid4

from brainy.interfaces.api import _calendar_event, _extract_events, _read_events, _save_event


def test_document_extraction_finds_each_dated_event():
    events = _extract_events(
        """Examen de Machine Learning :
20 septembre 2026 à 14h00

Rendu du rapport PFA :
22 septembre 2026 à 23h59

Présentation du projet :
24 septembre 2026 à 10h00""",
        "document",
    )

    assert [(event.title, event.date, event.time) for event in events] == [
        ("Examen de Machine Learning", "2026-09-20", "14:00"),
        ("Rendu du rapport PFA", "2026-09-22", "23:59"),
        ("Présentation du projet", "2026-09-24", "10:00"),
    ]


def test_photo_ocr_extraction_keeps_location_and_subject():
    events = _extract_events(
        """Réunion de projet
Date : 21 septembre 2026
Heure : 15h30
Lieu : Salle B12
Sujet : Présentation du prototype Brainy""",
        "photo",
    )

    assert len(events) == 1
    assert events[0].model_dump() == {
        "title": "Réunion de projet", "date": "2026-09-21", "time": "15:30", "end_time": None,
        "location": "Salle B12", "description": "Présentation du prototype Brainy", "source": "photo",
    }


def test_markdown_image_summary_is_split_into_clean_calendar_fields():
    events = _extract_events(
        """* **Date :** 21 septembre 2026
* **Heure :** 15h30
* **Lieu :** Salle B12
* **Sujet :** Réunion de projet – Présentation du prototype Brainy""",
        "photo",
    )

    assert events[0].model_dump() == {
        "title": "Réunion de projet", "date": "2026-09-21", "time": "15:30", "end_time": None,
        "location": "Salle B12", "description": "Présentation du prototype Brainy", "source": "photo",
    }


def test_date_without_event_intent_is_ignored():
    assert _extract_events("Le projet a été créé le 20 septembre 2026.", "document") == []


def test_sqlite_event_storage_deduplicates_imports():
    title = f"Examen {uuid4().hex}"
    extracted = _extract_events(f"{title} le 20 septembre 2026 à 14h.", "document")[0]
    event = _calendar_event(extracted, source_id="test.txt", source_label="Document : test.txt")

    assert _save_event(event)[1] is True
    assert _save_event(event)[1] is False
    assert len([saved for saved in _read_events() if saved["title"] == event.title and saved["start"] == event.start]) == 1
