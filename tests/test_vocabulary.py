"""Guards on the vocabulary configuration.

These tests are the reason the repository cannot quietly drift into claiming things it
has not earned: every enabled sign must carry a real source, and nobody may mark a sign
"verified" without naming a real reviewer.
"""
import json

import pytest

from sanket_setu.config import (
    CONFIG_PATH,
    blocked,
    load_excluded,
    load_signs,
    trainable,
    unverified,
)


@pytest.fixture(scope="module")
def signs():
    return load_signs()[1]


def test_config_is_valid_json_and_has_required_keys():
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for key in ("config_version", "signs", "staff_phrases", "dictionary"):
        assert key in raw, f"missing top-level key: {key}"
    assert raw["dictionary"]["format"], "the dictionary reference must state its format"


def test_every_enabled_sign_has_a_source_url(signs):
    for s in trainable(signs):
        if s.sign_type == "background":
            continue
        assert s.source_url.startswith("https://"), f"{s.id} has no real source URL"
        assert s.dictionary_category, f"{s.id} has no dictionary category"
        assert s.type_evidence, f"{s.id} has no recorded evidence for its sign type"


def test_no_sign_is_claimed_verified_without_a_real_validator(signs):
    """A sign may only be 'verified' if a human actually signed off on it."""
    for s in signs:
        if s.validation_status == "verified":
            assert s.validator and s.validator.lower() not in {
                "not yet reviewed", "n/a", "unknown", "tbd", "",
            }, f"{s.id} is marked verified but has no named validator"


def test_verified_signs_must_have_a_checklist_completed(signs):
    for s in signs:
        if s.validation_status == "verified":
            assert s.verification_checklist, f"{s.id} is verified but records no verification checklist"


def test_enabled_signs_are_static_single_hand_or_background(signs):
    for s in trainable(signs):
        assert s.sign_type in ("static_single_hand", "background"), \
            f"{s.id} is enabled but is a {s.sign_type} sign"


def test_pending_signs_are_disabled_and_explained(signs):
    for s in blocked(signs):
        assert s.notes, f"{s.id} is disabled with no explanation"
        assert s.type_confidence in ("low", "medium", "unknown"), \
            f"{s.id} is disabled but claims {s.type_confidence} type confidence"
        assert s.verification_checklist, f"{s.id} is disabled but has no verification checklist"


def test_unverified_lists_the_enabled_signs_awaiting_review(signs):
    pending = {s.id for s in unverified(signs)}
    enabled = {s.id for s in trainable(signs) if s.sign_type != "background"}
    assert pending == enabled, "every enabled sign must still be flagged as awaiting human review"


def test_excluded_signs_all_carry_a_reason():
    for e in load_excluded():
        assert e["reason"] and len(e["reason"]) > 40, f"{e['id']} has no real reason for exclusion"
        assert e["source_url"].startswith("https://")


def test_excluded_signs_do_not_overlap_the_enabled_vocabulary(signs):
    enabled = {s.id for s in trainable(signs)}
    for e in load_excluded():
        assert e["id"] not in enabled, f"{e['id']} is both enabled and excluded"


def test_staff_phrases_are_present_and_bilingual():
    from sanket_setu.config import load_phrases

    phrases = load_phrases()
    assert len(phrases) >= 5
    for p in phrases:
        assert p["text_hi"] and p["text_en"]
