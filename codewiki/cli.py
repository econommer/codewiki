"""CLI entry point for the cw command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from codewiki import config, frontmatter, meta, setup


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_init() -> None:
    """Initialize a wiki for the current repo."""
    repo_path = Path.cwd()
    wiki = config.wiki_path(repo_path)

    if wiki.exists():
        m = meta.WikiMeta.load(wiki)
        print(f"Wiki already exists at {wiki}")
        if m.last_compiled_commit:
            print(f"Last compiled: {m.last_compiled_commit[:7]}")
        else:
            print("Not yet compiled")
        return

    subdirs = ["modules", "concepts", "decisions", "learnings", "queries"]
    for d in subdirs:
        (wiki / d).mkdir(parents=True, exist_ok=True)

    project = config.project_name(repo_path)
    m = meta.WikiMeta(project=project, repo_path=str(repo_path))
    m.save(wiki)

    print(f"Initialized wiki at {wiki}")
    print(f"Project: {project}")
    print()
    print("Wiki is ready for compilation. Subdirectories created:")
    for d in subdirs:
        print(f"  {d}/")


def cmd_status() -> None:
    """Show what changed since last compile."""
    repo_path = Path.cwd()
    wiki = config.wiki_path(repo_path)

    if not wiki.exists():
        print("No wiki found. Run `cw init` first.")
        return

    m = meta.WikiMeta.load(wiki)

    if not m.last_compiled_commit:
        print("Wiki has not been compiled yet.")
        print("Run a full compile to generate articles.")
        return

    last_commit = m.last_compiled_commit

    result = subprocess.run(
        ["git", "diff", "--name-only", f"{last_commit}..HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Last compiled commit {last_commit[:7]} no longer in history.")
        print("Full recompile recommended.")
        return

    changed_files = [line for line in result.stdout.splitlines() if line.strip()]

    if not changed_files:
        print("Wiki is up to date.")
        return

    print(f"Changed since last compile ({last_commit[:7]}):")
    for f in changed_files:
        print(f"  M {f}")

    # Find stale articles
    stale_articles: list[str] = []
    for md_path in wiki.rglob("*.md"):
        try:
            content = md_path.read_text()
        except OSError:
            continue
        fm = frontmatter.parse(content)
        if fm and fm.source_files:
            if any(s in changed_files for s in fm.source_files):
                rel = md_path.relative_to(wiki)
                stale_articles.append(str(rel))

    if stale_articles:
        print()
        print("Stale articles:")
        for a in stale_articles:
            print(f"  ! {a}")


def cmd_meta_update() -> None:
    """Update wiki metadata with current commit."""
    repo_path = Path.cwd()
    wiki = config.wiki_path(repo_path)

    if not wiki.exists():
        print("No wiki found. Run `cw init` first.", file=sys.stderr)
        sys.exit(1)

    m = meta.WikiMeta.load(wiki)
    commit = meta.current_commit(repo_path)

    m.last_compiled_commit = commit
    m.last_compiled_at = datetime.now(timezone.utc)
    m.save(wiki)

    print(f"Updated meta: commit {commit[:7]}")


def cmd_index() -> None:
    """Rebuild _index.md from article frontmatter."""
    repo_path = Path.cwd()
    wiki = config.wiki_path(repo_path)

    if not wiki.exists():
        print("No wiki found. Run `cw init` first.", file=sys.stderr)
        sys.exit(1)

    entries: list[tuple[str, str, str]] = []  # (type, path, title)

    for md_path in sorted(wiki.rglob("*.md")):
        rel = md_path.relative_to(wiki)
        rel_str = str(rel)

        # Skip index and other underscore-prefixed files
        if rel_str.startswith("_"):
            continue

        try:
            content = md_path.read_text()
        except OSError:
            continue

        fm = frontmatter.parse(content)
        if fm:
            title = fm.title or rel_str
            article_type = fm.article_type or "unknown"
            entries.append((article_type, rel_str, title))

    entries.sort(key=lambda e: (e[0], e[2]))

    index_lines = ["# Wiki Index\n"]
    current_type = ""

    for article_type, path, title in entries:
        if article_type != current_type:
            current_type = article_type
            index_lines.append(f"\n## {current_type.capitalize()}\n")
        link_name = path.removesuffix(".md")
        index_lines.append(f"- [[{link_name}|{title}]]")

    if not entries:
        index_lines.append("\n_No articles yet. Wiki needs compilation._")

    index_path = wiki / "_index.md"
    index_path.write_text("\n".join(index_lines) + "\n")
    print(f"Index updated: {len(entries)} articles")


def cmd_projects() -> None:
    """List all wiki projects."""
    home = config.wiki_home()
    if not home.exists():
        print("No wikis found. Run `cw init` in a repo.")
        return

    found = False
    entries = sorted(
        [e for e in home.iterdir() if e.is_dir()],
        key=lambda e: e.name,
    )

    for entry in entries:
        meta_path = entry / "_meta.yaml"
        if meta_path.exists():
            try:
                m = meta.WikiMeta.load(entry)
            except Exception:
                continue
            found = True
            if m.last_compiled_commit:
                status = f"compiled ({m.last_compiled_commit[:7]})"
            else:
                status = "not compiled"
            print(f"  {m.project} - {m.repo_path} [{status}]")

    if not found:
        print("No wikis found. Run `cw init` in a repo.")


def cmd_path() -> None:
    """Print wiki path for current repo."""
    repo_path = Path.cwd()
    wiki = config.wiki_path(repo_path)
    print(wiki)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cw",
        description="Manage LLM-compiled code wikis",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("init", help="Initialize a wiki for the current repo")
    subparsers.add_parser("status", help="Show what changed since last compile")
    subparsers.add_parser("index", help="Rebuild _index.md from article frontmatter")
    subparsers.add_parser("projects", help="List all wiki projects")
    subparsers.add_parser("path", help="Print wiki path for current repo")

    # meta subcommand
    meta_parser = subparsers.add_parser("meta", help="Update wiki metadata")
    meta_sub = meta_parser.add_subparsers(dest="meta_action")
    meta_sub.add_parser("update", help="Record current commit as compiled")

    # setup subcommand
    setup_parser = subparsers.add_parser(
        "setup", help="Set up codewiki for an agent or tool"
    )
    setup_sub = setup_parser.add_subparsers(dest="setup_target")
    setup_sub.add_parser("claude-code", help="Install skill for Claude Code")
    setup_sub.add_parser("codex", help="Install instructions for Codex")
    setup_sub.add_parser("copilot", help="Install instructions for GitHub Copilot")
    setup_sub.add_parser("qmd", help="Add codewiki collection to QMD search")

    # uninstall subcommand
    uninstall_parser = subparsers.add_parser(
        "uninstall", help="Remove codewiki from an agent or tool"
    )
    uninstall_sub = uninstall_parser.add_subparsers(dest="uninstall_target")
    uninstall_sub.add_parser("claude-code", help="Remove from Claude Code")
    uninstall_sub.add_parser("codex", help="Remove from Codex")
    uninstall_sub.add_parser("copilot", help="Remove from GitHub Copilot")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "init":
            cmd_init()
        elif args.command == "status":
            cmd_status()
        elif args.command == "index":
            cmd_index()
        elif args.command == "projects":
            cmd_projects()
        elif args.command == "path":
            cmd_path()
        elif args.command == "meta":
            if not args.meta_action:
                print("Usage: cw meta update", file=sys.stderr)
                sys.exit(1)
            if args.meta_action == "update":
                cmd_meta_update()
        elif args.command == "setup":
            if not args.setup_target:
                print(
                    "Usage: cw setup {claude-code,codex,copilot,qmd}",
                    file=sys.stderr,
                )
                sys.exit(1)
            if args.setup_target == "claude-code":
                setup.setup_claude_code()
            elif args.setup_target == "codex":
                setup.setup_codex()
            elif args.setup_target == "copilot":
                setup.setup_copilot()
            elif args.setup_target == "qmd":
                setup.setup_qmd()
        elif args.command == "uninstall":
            if not args.uninstall_target:
                print(
                    "Usage: cw uninstall {claude-code,codex,copilot}",
                    file=sys.stderr,
                )
                sys.exit(1)
            if args.uninstall_target == "claude-code":
                setup.uninstall_claude_code()
            elif args.uninstall_target == "codex":
                setup.uninstall_codex()
            elif args.uninstall_target == "copilot":
                setup.uninstall_copilot()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
