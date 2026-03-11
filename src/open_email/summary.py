"""Generate template-based summaries of agent actions."""

from collections import Counter

def generate_summary(actions_taken: list[str]) -> str:
    """Generate a human-readable summary from a list of actions."""
    if not actions_taken:
        return "No actions taken in this cycle."

    summary_lines = []
    counts = Counter(actions_taken)

    for action, count in counts.items():
        if count > 1:
            summary_lines.append(f"- {action} ({count} times)")
        else:
            summary_lines.append(f"- {action}")

    return "\n".join(summary_lines)