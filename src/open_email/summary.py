"""Generate template-based summaries of agent actions."""

from collections import Counter

def generate_summary(stats) -> str:
    """Generate a human-readable summary from an AgentStats object."""
    summary_lines = []
    
    summary_lines.append("=== Agent Session Stats ===")
    summary_lines.append(f"Uptime: {stats.uptime}")
    summary_lines.append(f"Cycles Completed: {stats.cycles_completed}")
    summary_lines.append(f"Connected Accounts: {stats.accounts_connected}")
    summary_lines.append(f"Total Emails Processed: {stats.emails_processed}")
    summary_lines.append(f"Total Rules Triggered: {stats.rules_triggered}")
    summary_lines.append(f"Total Errors: {stats.errors}")
    summary_lines.append("")
    summary_lines.append("=== Cycle Actions ===")
    
    if not stats.actions_taken:
        summary_lines.append("No rule actions taken in this specific cycle.")
        return "\n".join(summary_lines)

    counts = Counter(stats.actions_taken)
    for action, count in counts.items():
        if count > 1:
            summary_lines.append(f"- {action} ({count} times)")
        else:
            summary_lines.append(f"- {action}")

    return "\n".join(summary_lines)