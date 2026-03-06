"""Rule engine: evaluate email rules against parsed emails."""

import fnmatch
import logging

from open_email.email_parser import ParsedEmail

logger = logging.getLogger(__name__)


def _normalize_to_list(value) -> list[str]:
    """Normalize a match value to a list of strings."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _match_field(pattern_or_keywords: list[str], field_value: str) -> bool:
    """Check if any pattern/keyword matches the field value.

    For 'from' and 'to' fields, uses glob matching (e.g. *@domain.com).
    For 'subject' and 'body' fields, uses case-insensitive substring matching.
    """
    field_lower = field_value.lower()
    for pattern in pattern_or_keywords:
        pattern_lower = pattern.lower()
        # If pattern contains glob characters, use fnmatch
        if "*" in pattern or "?" in pattern:
            if fnmatch.fnmatch(field_lower, pattern_lower):
                return True
        else:
            # Substring match
            if pattern_lower in field_lower:
                return True
    return False


def evaluate_rules(
    parsed_email: ParsedEmail,
    rules: list[dict],
    ai_classifier=None,
    first_match_only: bool = True,
) -> list[dict]:
    """Evaluate rules against a parsed email, return matching rules' actions.

    Args:
        parsed_email: The parsed email to evaluate.
        rules: List of rule dicts from config.
        ai_classifier: Optional AI classifier instance for ai_prompt rules.
        first_match_only: If True, return after first matching rule.

    Returns:
        List of dicts with 'name' and 'action' for each matching rule.
    """
    matches = []

    for rule in rules:
        name = rule["name"]
        match = rule["match"]
        action = rule["action"]

        if _rule_matches(parsed_email, match, ai_classifier, name):
            logger.info("Rule '%s' matched email UID %d (subject: %s)", name, parsed_email.uid, parsed_email.subject)
            matches.append({"name": name, "action": action})
            if first_match_only:
                break

    return matches


def _rule_matches(
    parsed_email: ParsedEmail,
    match: dict,
    ai_classifier,
    rule_name: str,
) -> bool:
    """Check if all conditions in a rule's match section are satisfied (AND logic)."""
    field_map = {
        "from": parsed_email.from_addr,
        "to": parsed_email.to_addr,
        "subject": parsed_email.subject,
        "body": parsed_email.body_text,
    }

    for key, patterns in match.items():
        if key == "ai_prompt":
            if not _evaluate_ai_condition(parsed_email, patterns, ai_classifier, rule_name):
                return False
            continue

        field_value = field_map.get(key, "")
        pattern_list = _normalize_to_list(patterns)
        if not _match_field(pattern_list, field_value):
            return False

    return True


def _evaluate_ai_condition(
    parsed_email: ParsedEmail,
    prompt: str,
    ai_classifier,
    rule_name: str,
) -> bool:
    """Evaluate an AI-based rule condition."""
    if ai_classifier is None or not ai_classifier.is_available():
        logger.debug("AI classifier not available, skipping rule '%s'", rule_name)
        return False

    email_content = f"From: {parsed_email.from_addr}\nSubject: {parsed_email.subject}\n\n{parsed_email.body_text[:2000]}"
    try:
        return ai_classifier.classify(prompt, email_content)
    except Exception as e:
        logger.warning("AI classification failed for rule '%s': %s", rule_name, e)
        return False
