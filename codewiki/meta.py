"""Wiki metadata management."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml


class WikiMeta:
    """Represents the _meta.yaml file for a wiki project."""

    def __init__(
        self,
        project: str,
        repo_path: str,
        last_compiled_commit: Optional[str] = None,
        last_compiled_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ):
        self.project = project
        self.repo_path = repo_path
        self.last_compiled_commit = last_compiled_commit
        self.last_compiled_at = last_compiled_at
        self.created_at = created_at or datetime.now(timezone.utc)

    @classmethod
    def load(cls, wiki_path: Path) -> "WikiMeta":
        """Load _meta.yaml from a wiki directory."""
        meta_path = wiki_path / "_meta.yaml"
        content = meta_path.read_text()
        data = yaml.safe_load(content)

        return cls(
            project=data["project"],
            repo_path=data["repo_path"],
            last_compiled_commit=data.get("last_compiled_commit"),
            last_compiled_at=data.get("last_compiled_at"),
            created_at=data.get("created_at", datetime.now(timezone.utc)),
        )

    def save(self, wiki_path: Path) -> None:
        """Save _meta.yaml to a wiki directory."""
        meta_path = wiki_path / "_meta.yaml"
        data = {
            "project": self.project,
            "repo_path": self.repo_path,
            "last_compiled_commit": self.last_compiled_commit,
            "last_compiled_at": self.last_compiled_at,
            "created_at": self.created_at,
        }
        meta_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


def current_commit(repo_path: Path) -> str:
    """Get current HEAD commit hash from the repo."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Not a git repository or no commits yet")
    return result.stdout.strip()
