"""Generate template-based summaries of agent actions."""

from collections import Counter

def generate_summary(stats, rules: list[dict] = None) -> str:
    """Generate a human-readable summary from an AgentStats object."""
    lines = []
    
    lines.append("════════════════════════════════════════════════════════")
    lines.append(f"                 CYCLE SUMMARY                  ")
    lines.append("════════════════════════════════════════════════════════")
    lines.append(f"  Uptime:       {stats.uptime}")
    lines.append(f"  Cycles:       {stats.cycles_completed}")
    lines.append(f"  Accounts:     {stats.accounts_connected}")
    lines.append(f"  Processed:    {stats.emails_processed}")
    lines.append(f"  Exceptions:   {stats.errors}")
    lines.append("")
    
    if rules is not None:
        custom_r = []
        system_r = []
        for r in rules:
            if r["name"] in ("auto-sort-by-sender", "content-based-rules", "office-based-rules"):
                if r["name"] == "auto-sort-by-sender" and r.get("action", {}).get("auto_sort_by_sender"):
                    system_r.append("Auto-Sort by Sender")
                elif r["name"] == "content-based-rules":
                    for name, cfg in r.get("action", {}).get("content_based_rules", {}).items():
                        if cfg.get("enabled"):
                            system_r.append(f"[Content] {name}")
                elif r["name"] == "office-based-rules":
                    for name, cfg in r.get("action", {}).get("office_based_rules", {}).items():
                        if cfg.get("enabled"):
                            system_r.append(f"[Office]  {name}")
            else:
                custom_r.append(r["name"])
        
        lines.append("── Active Rules ────────────────────────────────────────")
        if custom_r:
            lines.append(f"  User Rules ({len(custom_r)}):")
            for c in custom_r:
                lines.append(f"    - {c}")
        if system_r:
            lines.append(f"  System Rules ({len(system_r)}):")
            for s in system_r:
                lines.append(f"    - {s}")
        if not custom_r and not system_r:
            lines.append("  (No rules currently active)")
        lines.append("")

    lines.append("── Cycle Activity ──────────────────────────────────────")
    if getattr(stats, "rules_triggered_this_cycle", None):
        lines.append("  Rules Triggered This Cycle:")
        for r_name, count in sorted(stats.rules_triggered_this_cycle.items(), key=lambda x: -x[1]):
            lines.append(f"    ✓ {r_name} (x{count})")
        lines.append("")

    if not stats.actions_taken:
        lines.append("  No specific file manipulations or actions taken.")
    else:
        lines.append("  Actions Performed:")
        counts = Counter(stats.actions_taken)
        for action, count in counts.items():
            lines.append(f"    -> {action} (x{count})" if count > 1 else f"    -> {action}")

    lines.append("════════════════════════════════════════════════════════")
    return "\n".join(lines)