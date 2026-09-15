import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def bootstrap_agents(registry):
    """Validate agent registry entries and log a startup summary.

    Returns a dict with counts and lists for programmatic checks.
    """
    total = 0
    missing_profiles = []
    for agent_id, entry in registry.items():
        total += 1
        profile_path = entry.get("profile_path")
        if profile_path is None:
            missing_profiles.append((agent_id, "missing profile_path"))
            continue
        p = Path(profile_path)
        if not p.exists():
            missing_profiles.append((agent_id, str(profile_path)))
    if missing_profiles:
        logger.warning(
            "Agent registry bootstrap: %d/%d profiles missing or unreadable",
            len(missing_profiles),
            total,
        )
        for aid, reason in missing_profiles:
            logger.warning(" - %s -> %s", aid, reason)
    else:
        logger.info("Agent registry bootstrap: all %d agent profiles present", total)
    return {
        "total": total,
        "missing_count": len(missing_profiles),
        "missing": missing_profiles,
    }
