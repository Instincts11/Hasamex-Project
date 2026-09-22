from pathlib import Path

import pytest

from app.services.guide_parser import GuideParseError, parse_guide, parse_guide_file


def test_parses_real_interview_guide(interview_guide_path: Path) -> None:
    guide = parse_guide_file(interview_guide_path)
    assert "European Robotic Surgery Market" in guide.title
    assert "hospital adoption" in guide.objective.lower()
    assert [question.number for question in guide.questions] == [1, 2, 3, 4, 5, 6]
    assert guide.questions[1].text == "What are the main barriers to adoption?"
    assert "timeline" in guide.questions[5].text.lower()


def test_does_not_invent_questions() -> None:
    with pytest.raises(GuideParseError, match="no questions"):
        parse_guide("Interview Guide\n\nProject objective:\nUnderstand adoption.\n")
