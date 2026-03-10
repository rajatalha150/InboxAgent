"""Tests for rule_engine module."""

from open_email.email_parser import ParsedEmail
from open_email.rule_engine import evaluate_rules


def _make_email(**kwargs) -> ParsedEmail:
    defaults = {
        "uid": 1,
        "from_addr": "sender@example.com",
        "to_addr": "me@example.com",
        "subject": "Hello World",
        "body_text": "This is a test email body.",
    }
    defaults.update(kwargs)
    return ParsedEmail(**defaults)


def _make_rule(name, match, action=None):
    return {"name": name, "match": match, "action": action or {"flag": True}}


class TestFromMatching:
    def test_exact_match(self):
        email = _make_email(from_addr="alerts@verizon.com")
        rules = [_make_rule("verizon", {"from": "alerts@verizon.com"}, {"move_to": "Verizon"})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 1
        assert matches[0]["name"] == "verizon"

    def test_glob_match(self):
        email = _make_email(from_addr="billing@verizon.com")
        rules = [_make_rule("verizon", {"from": "*@verizon.com"}, {"move_to": "Verizon"})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 1

    def test_no_match(self):
        email = _make_email(from_addr="someone@gmail.com")
        rules = [_make_rule("verizon", {"from": "*@verizon.com"})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 0

    def test_case_insensitive(self):
        email = _make_email(from_addr="Alerts@VERIZON.COM")
        rules = [_make_rule("verizon", {"from": "*@verizon.com"})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 1

    def test_from_list(self):
        email = _make_email(from_addr="noreply@spammer.com")
        rules = [_make_rule("spam", {"from": ["noreply@spammer.com", "deals@junk.com"]})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 1


class TestSubjectMatching:
    def test_keyword_match(self):
        email = _make_email(subject="Your invoice for March")
        rules = [_make_rule("billing", {"subject": ["invoice", "billing"]})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 1

    def test_no_keyword_match(self):
        email = _make_email(subject="Meeting tomorrow")
        rules = [_make_rule("billing", {"subject": ["invoice", "billing"]})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 0

    def test_case_insensitive(self):
        email = _make_email(subject="INVOICE attached")
        rules = [_make_rule("billing", {"subject": "invoice"})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 1


class TestAndLogic:
    def test_all_conditions_must_match(self):
        email = _make_email(from_addr="noreply@spammer.com", subject="Limited offer inside!")
        rules = [_make_rule("spam", {"from": ["noreply@spammer.com"], "subject": ["limited offer"]})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 1

    def test_partial_match_fails(self):
        email = _make_email(from_addr="noreply@spammer.com", subject="Hello friend")
        rules = [_make_rule("spam", {"from": ["noreply@spammer.com"], "subject": ["limited offer"]})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 0


class TestFirstMatchWins:
    def test_first_match_only(self):
        email = _make_email(from_addr="alerts@verizon.com", subject="Your invoice")
        rules = [
            _make_rule("verizon", {"from": "*@verizon.com"}, {"move_to": "Verizon"}),
            _make_rule("billing", {"subject": "invoice"}, {"move_to": "Invoices"}),
        ]
        matches = evaluate_rules(email, rules, first_match_only=True)
        assert len(matches) == 1
        assert matches[0]["name"] == "verizon"

    def test_all_matches(self):
        email = _make_email(from_addr="alerts@verizon.com", subject="Your invoice")
        rules = [
            _make_rule("verizon", {"from": "*@verizon.com"}, {"move_to": "Verizon"}),
            _make_rule("billing", {"subject": "invoice"}, {"move_to": "Invoices"}),
        ]
        matches = evaluate_rules(email, rules, first_match_only=False)
        assert len(matches) == 2


class TestAIRules:
    def test_ai_rule_skipped_without_classifier(self):
        email = _make_email(subject="Job opportunity at Google")
        rules = [_make_rule("jobs", {"ai_prompt": "Is this about a job?"}, {"move_to": "Jobs"})]
        matches = evaluate_rules(email, rules, ai_classifier=None)
        assert len(matches) == 0

    def test_ai_rule_with_mock_classifier(self):
        class MockClassifier:
            def is_available(self):
                return True
            def classify(self, prompt, content):
                return True

        email = _make_email(subject="Job opportunity at Google")
        rules = [_make_rule("jobs", {"ai_prompt": "Is this about a job?"}, {"move_to": "Jobs"})]
        matches = evaluate_rules(email, rules, ai_classifier=MockClassifier())
        assert len(matches) == 1

    def test_ai_rule_negative(self):
        class MockClassifier:
            def is_available(self):
                return True
            def classify(self, prompt, content):
                return False

        email = _make_email(subject="Lunch plans")
        rules = [_make_rule("jobs", {"ai_prompt": "Is this about a job?"}, {"move_to": "Jobs"})]
        matches = evaluate_rules(email, rules, ai_classifier=MockClassifier())
        assert len(matches) == 0


class TestBodyMatching:
    def test_body_keyword_match(self):
        email = _make_email(body_text="Please find the attached invoice for your records.")
        rules = [_make_rule("billing", {"body": "invoice"})]
        matches = evaluate_rules(email, rules)
        assert len(matches) == 1
