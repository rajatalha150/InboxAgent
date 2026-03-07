"""Load and validate YAML configuration files."""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

REQUIRED_ACCOUNT_FIELDS = {"name", "imap_server", "email", "password"}
VALID_MATCH_FIELDS = {"from", "to", "subject", "body", "ai_prompt"}
VALID_ACTION_FIELDS = {"move_to", "flag", "delete", "mark_read", "mark_unread", "label", "auto_sort_by_sender"}


def load_yaml(path: Path) -> dict:
    """Load a YAML file and return its contents as a dict."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def load_accounts(path: Path) -> list[dict]:
    """Load and validate accounts configuration."""
    data = load_yaml(path)
    accounts = data.get("accounts")
    if not accounts or not isinstance(accounts, list):
        raise ValueError(f"No 'accounts' list found in {path}")

    validated = []
    for i, account in enumerate(accounts):
        missing = REQUIRED_ACCOUNT_FIELDS - set(account.keys())
        if missing:
            raise ValueError(f"Account #{i + 1} missing required fields: {missing}")

        validated.append({
            "name": account["name"],
            "imap_server": account["imap_server"],
            "imap_port": account.get("imap_port", 993),
            "email": account["email"],
            "password": account["password"],
            "ssl": account.get("ssl", True),
        })

    logger.info("Loaded %d account(s)", len(validated))
    return validated


def load_rules(path: Path) -> list[dict]:
    """Load and validate rules configuration."""
    data = load_yaml(path)
    rules = data.get("rules")
    if not rules or not isinstance(rules, list):
        raise ValueError(f"No 'rules' list found in {path}")

    validated = []
    for i, rule in enumerate(rules):
        name = rule.get("name", f"rule-{i + 1}")
        match = rule.get("match")
        action = rule.get("action")

        if not match or not isinstance(match, dict):
            raise ValueError(f"Rule '{name}' missing 'match' section")
        if not action or not isinstance(action, dict):
            raise ValueError(f"Rule '{name}' missing 'action' section")

        unknown_match = set(match.keys()) - VALID_MATCH_FIELDS
        if unknown_match:
            raise ValueError(f"Rule '{name}' has unknown match fields: {unknown_match}")

        unknown_action = set(action.keys()) - VALID_ACTION_FIELDS
        if unknown_action:
            raise ValueError(f"Rule '{name}' has unknown action fields: {unknown_action}")

        validated.append({
            "name": name,
            "match": match,
            "action": action,
        })

    logger.info("Loaded %d rule(s)", len(validated))
    return validated


def save_accounts(path: Path, accounts: list[dict]) -> None:
    """Write accounts list back to YAML config file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump({"accounts": accounts}, f, default_flow_style=False, sort_keys=False)
    logger.info("Saved %d account(s) to %s", len(accounts), path)


def save_rules(path: Path, rules: list[dict]) -> None:
    """Write rules list back to YAML config file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump({"rules": rules}, f, default_flow_style=False, sort_keys=False)
    logger.info("Saved %d rule(s) to %s", len(rules), path)
