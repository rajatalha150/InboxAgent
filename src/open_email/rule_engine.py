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
    """Evaluate rules against a parsed email, return matching rules' actions."""
    matches = []

    # Separate rules for prioritized execution
    custom_rules = [r for r in rules if r["name"] not in ("auto-sort-by-sender", "content-based-rules")]
    auto_sort_rule = next((r for r in rules if r["name"] == "auto-sort-by-sender"), None)
    content_rules_container = next((r for r in rules if r["name"] == "content-based-rules"), None)

    # 1. Custom rules take highest priority
    for rule in custom_rules:
        if _rule_matches(parsed_email, rule["match"], ai_classifier, rule["name"]):
            logger.info("Rule '%s' matched email UID %d (subject: %s)", rule["name"], parsed_email.uid, parsed_email.subject)
            matches.append({"name": rule["name"], "action": rule["action"]})
            if first_match_only:
                return matches

    # If any custom rules matched, they take precedence and we're done.
    if matches:
        return matches

    # 2. Content-based rules are next (only if no custom rules matched)
    if content_rules_container:
        content_based_rules = content_rules_container.get("action", {}).get("content_based_rules", {})
        content_matches = _evaluate_content_based_rules(parsed_email, content_based_rules)
        if content_matches:
            return content_matches

    # 3. Auto-sort is the final catch-all (only if nothing else matched)
    if auto_sort_rule:
        if _rule_matches(parsed_email, auto_sort_rule["match"], ai_classifier, auto_sort_rule["name"]):
            logger.info("Rule '%s' matched email UID %d (subject: %s)", auto_sort_rule["name"], parsed_email.uid, parsed_email.subject)
            matches.append({"name": auto_sort_rule["name"], "action": auto_sort_rule["action"]})
            return matches

    return matches

def _evaluate_content_based_rules(parsed_email: ParsedEmail, config: dict) -> list[dict]:
    """Evaluate content-based rules and return actions for matching rules."""
    matches = []
    for rule_name, rule_config in config.items():
        if not rule_config.get("enabled", False):
            continue

        keywords = rule_config.get("keywords", {})
        for condition, kws in keywords.items():
            field_value = ""
            if condition == "from":
                field_value = parsed_email.from_addr
            elif condition == "subject":
                field_value = parsed_email.subject

            if field_value and _match_field(kws, field_value):
                action = {}
                if rule_name == "Promotions & Social":
                    action["move_to"] = "Promotions"
                elif rule_name == "High-Priority":
                    action["flag"] = True
                elif rule_name == "Junk":
                    action["move_to"] = "Junk"
                elif rule_name == "Calendar":
                    action["move_to"] = "Calendar"
                
                if action:
                    matches.append({"name": f"content-based: {rule_name}", "action": action})
                    # Stop after first match within content-based rules for this email
                    return matches
    return matches



def _rule_matches(
    parsed_email: ParsedEmail,
    match: dict,
    ai_classifier,
    rule_name: str,
) -> bool:
    """Check if all conditions in a rule's match section are satisfied (AND logic)."""
    # Date parsing
    now = datetime.now(timezone.utc)
    email_date = None
    try:
        email_date = email.utils.parsedate_to_datetime(parsed_email.date)
        if email_date.tzinfo is None:
            email_date = email_date.replace(tzinfo=timezone.utc)  # Assume UTC if no timezone
    except (TypeError, ValueError):
        logger.warning("Could not parse email date: %s", parsed_email.date)

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

        if key == "days_older":
            if email_date and int(patterns) > 0:
                if (now - email_date).days < int(patterns):
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
