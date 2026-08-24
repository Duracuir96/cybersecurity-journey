# src/dashboard/playbooks.py
#
# Reads response playbooks from data/playbooks/<key>.md.
# The .md files in the repo are the single source of truth; the app renders them.

import os
import functools


def _candidate_dirs():
    """Places where data/playbooks might live, most reliable first."""
    here = os.path.dirname(os.path.abspath(__file__))          # src/dashboard
    project_root = os.path.dirname(os.path.dirname(here))       # project root
    return [
        os.path.join(project_root, "data", "playbooks"),
        os.path.join(os.getcwd(), "data", "playbooks"),
        os.path.join(os.getcwd(), "..", "data", "playbooks"),
    ]


@functools.lru_cache(maxsize=None)
def load_playbook(key):
    """
    Returns the markdown of the playbook for a detection key, or a fallback
    message if no file exists. Cached so each file is read once per session.
    """
    for d in _candidate_dirs():
        path = os.path.join(d, f"{key}.md")
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    return (
        "_No playbook file found for this detection._\n\n"
        "Review the matched events and follow your organisation's incident "
        "response procedure."
    )