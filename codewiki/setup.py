"""Agent and tool setup/uninstall helpers."""

from __future__ import annotations

import subprocess
from importlib import resources
from pathlib import Path

from codewiki import config

# ---------------------------------------------------------------------------
# Skill content (embedded)
# ---------------------------------------------------------------------------

_SKILL_DIR = Path(__file__).resolve().parent.parent / "skills"


def _read_skill(filename: str) -> str:
    return (_SKILL_DIR / filename).read_text()


CODEX_AGENTS_SECTION = """

## CodeWiki — Codebase Knowledge

You have a compiled wiki of this codebase at `~/.codewiki/`. Use it.

### Session start — MANDATORY

Before doing any work, check the wiki state:

```bash
cw status
```

If the wiki is stale or uncompiled, update it:
- Read changed source files
- Update the corresponding wiki articles in `~/.codewiki/<project>/`
- Run `cw index` then `cw meta update`

If no wiki exists, run `cw init` and compile from scratch.

### During work

When you need to understand how a module works, read the wiki article first:
```bash
cat ~/.codewiki/<project>/modules/<name>.md
```

### Session end — MANDATORY

Before finishing any task that involved code changes:

1. If you fixed a bug, create `~/.codewiki/<project>/learnings/<slug>.md`
2. If you made a design decision, create `~/.codewiki/<project>/decisions/<slug>.md`
3. Update any wiki articles affected by your code changes
4. Run `cw index` then `cw meta update`

### Article format

All wiki articles use YAML frontmatter:

```yaml
---
title: Module Name
type: module
source_files:
  - path/to/file
tags: [relevant, tags]
---
```

### Rules

- Check wiki before working. Update wiki before finishing. No exceptions.
- Write for a future agent with zero context.
- Include `source_files` in frontmatter so `cw status` can detect staleness.
"""

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _claude_home() -> Path:
    return Path.home() / ".claude"


def _codex_home() -> Path:
    return Path.home() / ".codex"


# ---------------------------------------------------------------------------
# Claude Code setup
# ---------------------------------------------------------------------------


def setup_claude_code() -> None:
    """Install codewiki skill for Claude Code."""
    skill_dir = _claude_home() / "skills" / "codewiki"
    skill_path = skill_dir / "SKILL.md"

    if skill_path.exists():
        print(f"Skill already installed at {skill_path}")
        print("Updating...")

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(_read_skill("codewiki-session.md"))

    print(f"Installed codewiki skill to {skill_path}")
    print()
    print("Claude Code will now use the codewiki skill to maintain")
    print("your codebase wiki at session start and end.")


# ---------------------------------------------------------------------------
# Codex setup
# ---------------------------------------------------------------------------


def setup_codex() -> None:
    """Install codewiki instructions for Codex."""
    home = _codex_home()
    agents_path = home / "AGENTS.md"

    existing = ""
    if agents_path.exists():
        existing = agents_path.read_text()

    if "## CodeWiki" in existing:
        print(f"CodeWiki already installed in {agents_path}")
        return

    home.mkdir(parents=True, exist_ok=True)
    content = existing.rstrip() + "\n" + CODEX_AGENTS_SECTION
    agents_path.write_text(content)

    print(f"Installed codewiki instructions to {agents_path}")


# ---------------------------------------------------------------------------
# GitHub Copilot setup
# ---------------------------------------------------------------------------


def setup_copilot() -> None:
    """Install codewiki instructions for GitHub Copilot.

    Creates .github/copilot-instructions.md in the current repository
    with the codewiki session skill.
    """
    repo_path = Path.cwd()
    github_dir = repo_path / ".github"
    instructions_path = github_dir / "copilot-instructions.md"

    existing = ""
    if instructions_path.exists():
        existing = instructions_path.read_text()

    if "## CodeWiki" in existing:
        print(f"CodeWiki already installed in {instructions_path}")
        return

    github_dir.mkdir(parents=True, exist_ok=True)

    copilot_skill = _read_skill("copilot-instructions.md")
    content = existing.rstrip() + "\n\n" + copilot_skill if existing.strip() else copilot_skill
    instructions_path.write_text(content)

    print(f"Installed codewiki instructions to {instructions_path}")
    print()
    print("GitHub Copilot will now use the codewiki skill to maintain")
    print("your codebase wiki during coding sessions.")


# ---------------------------------------------------------------------------
# QMD setup
# ---------------------------------------------------------------------------


def setup_qmd() -> None:
    """Add codewiki collection to QMD search."""
    wiki_home = config.wiki_home()

    if not wiki_home.exists():
        print(f"No wikis found at {wiki_home}.")
        print("Run `cw init` in a repo first.")
        return

    # Check if qmd is available
    try:
        result = subprocess.run(
            ["qmd", "--help"],
            capture_output=True,
        )
        if result.returncode != 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print("qmd not found in PATH.")
        print("Install QMD first: https://github.com/tobi/qmd")
        return

    # Add collection
    result = subprocess.run(
        ["qmd", "collection", "add", str(wiki_home), "--name", "codewiki"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"Added codewiki collection to QMD: {wiki_home}")
    else:
        if "already exists" in result.stderr:
            print("QMD collection 'codewiki' already exists.")
        else:
            print(f"QMD collection add output: {result.stdout}")
            if result.stderr:
                print(f"stderr: {result.stderr}")

    # Run embed to index
    print("Indexing wiki articles...")
    result = subprocess.run(
        ["qmd", "embed"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("QMD indexing complete.")
    else:
        print(f"QMD embed warning: {result.stderr}")

    print()
    print("You can now search your wiki:")
    print('  qmd query "how does auth work" -c codewiki')


# ---------------------------------------------------------------------------
# Uninstall helpers
# ---------------------------------------------------------------------------


def _remove_section(content: str, header: str) -> str:
    """Remove a markdown section starting with `header` until the next ## heading.

    Handles fenced code blocks (``` ) to avoid treating headings inside
    code blocks as section boundaries.
    """
    result: list[str] = []
    skipping = False
    in_code_block = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block

        if not in_code_block:
            if line.startswith(header):
                skipping = True
                continue
            if skipping and line.startswith("## "):
                skipping = False

        if not skipping:
            result.append(line)

    return "\n".join(result)


def uninstall_claude_code() -> None:
    """Remove codewiki from Claude Code."""
    skill_dir = _claude_home() / "skills" / "codewiki"
    if skill_dir.exists():
        import shutil

        shutil.rmtree(skill_dir)
        print("Removed codewiki skill from Claude Code.")
    else:
        print("Nothing to remove.")


def uninstall_codex() -> None:
    """Remove codewiki from Codex."""
    agents_path = _codex_home() / "AGENTS.md"
    if agents_path.exists():
        content = agents_path.read_text()
        if "## CodeWiki" in content:
            cleaned = _remove_section(content, "## CodeWiki")
            agents_path.write_text(cleaned.strip() + "\n")
            print("Removed codewiki from Codex AGENTS.md.")
        else:
            print("Nothing to remove.")
    else:
        print("Nothing to remove.")


def uninstall_copilot() -> None:
    """Remove codewiki from GitHub Copilot instructions."""
    repo_path = Path.cwd()
    instructions_path = repo_path / ".github" / "copilot-instructions.md"

    if instructions_path.exists():
        content = instructions_path.read_text()
        if "## CodeWiki" in content:
            cleaned = _remove_section(content, "## CodeWiki")
            cleaned = cleaned.strip()
            if cleaned:
                instructions_path.write_text(cleaned + "\n")
            else:
                instructions_path.unlink()
                print("Removed empty copilot-instructions.md.")
            print("Removed codewiki from GitHub Copilot instructions.")
        else:
            print("Nothing to remove.")
    else:
        print("Nothing to remove.")
