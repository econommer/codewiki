"""Wiki path and project name configuration."""

import subprocess
from pathlib import Path


def wiki_home() -> Path:
    """Base directory for all wikis: ~/.codewiki/"""
    return Path.home() / ".codewiki"


def project_name(repo_path: Path) -> str:
    """Derive project name from git remote origin URL, falling back to directory name."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            name = url.rsplit("/", 1)[-1]
            name = name.removesuffix(".git")
            if name:
                return name
    except FileNotFoundError:
        pass

    name = repo_path.name
    if not name:
        raise RuntimeError("Could not determine project name from directory")
    return name


def wiki_path(repo_path: Path) -> Path:
    """Full path to this project's wiki: ~/.codewiki/<project>/"""
    return wiki_home() / project_name(repo_path)
