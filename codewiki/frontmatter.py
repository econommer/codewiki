"""Parse YAML frontmatter from markdown files."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import yaml


@dataclass
class ArticleFrontmatter:
    title: Optional[str] = None
    article_type: Optional[str] = None
    source_files: Optional[list[str]] = None
    tags: Optional[list[str]] = None


def parse(content: str) -> Optional[ArticleFrontmatter]:
    """Parse YAML frontmatter from a markdown file's content.

    Returns None if no frontmatter found.
    """
    content = content.strip()
    if not content.startswith("---"):
        return None

    rest = content[3:]
    end = rest.find("\n---")
    if end == -1:
        return None

    yaml_str = rest[:end]
    data = yaml.safe_load(yaml_str)
    if not isinstance(data, dict):
        return None

    return ArticleFrontmatter(
        title=data.get("title"),
        article_type=data.get("type"),
        source_files=data.get("source_files"),
        tags=data.get("tags"),
    )
