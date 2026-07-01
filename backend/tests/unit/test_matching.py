"""
Unit tests for the Profile Match Rating scorer (app/services/matching.py).

Pure functions, no database or network — fast and deterministic.
"""

from app.services.matching import compute_match_score


def test_no_job_skills_returns_none():
    # A job with no listed skills can't be scored — the UI shows "not rated".
    assert compute_match_score({"Python"}, []) is None


def test_full_match_is_100():
    job = [
        {"skill": "Python", "importance": "critical"},
        {"skill": "React", "importance": "high"},
    ]
    assert compute_match_score({"Python", "React"}, job) == 100.0


def test_no_overlap_is_zero():
    assert compute_match_score({"Python"}, [{"skill": "Go", "importance": "high"}]) == 0.0


def test_partial_match_is_weighted_by_importance():
    # User has the critical skill (weight 3.0) but not the nice-to-have (weight 0.5):
    # achieved 3.0 / possible 3.5 = 85.7%. Also checks case-insensitive matching.
    job = [
        {"skill": "Python", "importance": "critical"},
        {"skill": "Figma", "importance": "nice-to-have"},
    ]
    assert compute_match_score({"python"}, job) == 85.7


def test_accepts_plain_string_skills():
    assert compute_match_score({"Python"}, ["Python"]) == 100.0
