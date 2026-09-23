from pathlib import Path

import pytest

from app.services.guide_parser import GuideParseError, parse_guide, parse_guide_file

SAMPLE_GUIDE = """Interview Guide – European Robotic Surgery Market

Project objective:
Understand hospital adoption, barriers, economics, and purchasing behaviour for robotic surgery systems in Europe.

Questions:
1. How would you describe current adoption of robotic surgery in your market?
2. What are the main barriers to adoption?
3. How important are hospital budgets and ROI in purchasing decisions?
4. How important are surgeon training and clinical outcomes?
5. What adoption trend do you expect over the next 3–5 years?
6. What is the typical hospital decision-making timeline for purchasing a new robotic system?
"""


def test_parses_interview_guide_text() -> None:
    guide = parse_guide(SAMPLE_GUIDE)
    assert "European Robotic Surgery Market" in guide.title
    assert "hospital adoption" in guide.objective.lower()
    assert [question.number for question in guide.questions] == [1, 2, 3, 4, 5, 6]
    assert guide.questions[1].text == "What are the main barriers to adoption?"
    assert "timeline" in guide.questions[5].text.lower()


def test_missing_guide_file_uses_case_questions(tmp_path: Path) -> None:
    guide = parse_guide_file(tmp_path / "Interview_Guide.txt")
    assert "European Robotic Surgery Market" in guide.title
    assert [question.number for question in guide.questions] == [1, 2, 3, 4, 5, 6]


def test_does_not_invent_questions() -> None:
    with pytest.raises(GuideParseError, match="no questions"):
        parse_guide("Interview Guide\n\nProject objective:\nUnderstand adoption.\n")
