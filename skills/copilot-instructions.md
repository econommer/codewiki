## CodeWiki — Codebase Knowledge (GitHub Copilot)

You have a compiled wiki of this codebase at `~/.codewiki/`. Use it to maintain persistent understanding across sessions.

### Session Start — MANDATORY

Before doing any work, check the wiki state:

```bash
cw status
```

**If no wiki exists** (first time):
1. Run `cw init`
2. Perform a full compile:
   - List all source files (respect .gitignore), group them by directory/module
   - For each module, read every file and write a wiki article at `~/.codewiki/<project>/modules/<name>.md`
   - Write cross-cutting articles in `concepts/`, `_architecture.md`, and `_patterns.md`
   - Run `cw index` then `cw meta update`

**If "not yet compiled":**
- Perform full compile as above

**If stale articles listed:**
- For each stale article, re-read the source files and update the article
- Run `cw index` then `cw meta update`

**If "up to date":**
- Skip, proceed with user's task

### During Work

When you need to understand how a module works, read the wiki article first:
```bash
cat ~/.codewiki/<project>/modules/<name>.md
```

### After Every Completed Task — MANDATORY

Do NOT wait until session end. After completing each task (bug fix, feature, refactor), immediately:

1. **Update affected wiki articles.** If you changed `src/auth/middleware.py` and `modules/auth.md` describes that file, update the article now.

2. **Write learnings.** If you fixed a bug, write `~/.codewiki/<project>/learnings/<slug>.md`:
   ```yaml
   ---
   title: <Short description>
   type: learning
   source_files: [affected files]
   tags: [relevant, tags]
   ---
   ```
   What happened, root cause, and fix.

3. **Write decisions.** If you made a design decision, write `~/.codewiki/<project>/decisions/<slug>.md`:
   ```yaml
   ---
   title: <Decision>
   type: decision
   tags: [relevant, tags]
   ---
   ```
   What was decided, why, and what alternatives were considered.

4. **Run `cw meta update`** to record the current commit.

### Session End

Run `cw index` to rebuild the master index.

### Article Format

Every article uses YAML frontmatter:

```markdown
---
title: <Module Name>
type: module
source_files:
  - path/to/file1
  - path/to/file2
tags: [relevant, tags]
---

## Overview
What this module does in 2-3 sentences.

## Key Components
List ALL functions/classes with line numbers and purpose.

## Data Flow
How data enters, transforms, and exits this module.

## Connections
Links to related modules: [[other-module]]

## Known Issues
Anything fragile, incomplete, or worth noting.
```

### Article Quality Rules

- List ALL fields on models/structs, including timestamps and metadata fields
- List ALL methods, including properties, `__str__`, `clean()`, `save()`
- Verify line numbers by reading the code, not guessing
- `source_files` must list EVERY file you read, including test files
- Use Obsidian `[[backlinks]]` to connect related articles
- Write for a future agent with zero context about this codebase
- When in doubt, include more detail, not less

### Architecture Diagrams

Include architecture diagrams in `_architecture.md` and module articles:
- Use UTF-8 box-drawing characters (`┌ ┐ └ ┘ ─ │ ► ◄ ▼ ▲`)
- Label every box with the component name AND its file/class
- Keep diagrams under 20 lines
- Wrap in ` ```text ` fenced blocks

### Rules

- Check wiki before working. Update wiki before finishing. No exceptions.
- Include `source_files` in frontmatter so `cw status` can detect staleness.
- A task isn't done until the wiki reflects what changed.
