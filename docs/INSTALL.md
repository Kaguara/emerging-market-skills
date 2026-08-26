# Install

These skills are markdown files with YAML frontmatter. Any tool that can read
instructions from a directory can use them; the sections below cover the common
ones.

Pin to a release tag rather than tracking `main`. These files are instructions to
an agent that probably has file and shell access in your environment, and they
deserve the same review discipline as any other dependency.

## Claude Code

The shortest path:

```
/plugin marketplace add Kaguara/emerging-market-skills
```

then:

```
/plugin install emerging-market-skills@kaguara
```

Skills load on demand — Claude reads each `description` and pulls in the full
skill only when the work matches. You do not need to invoke them by name, though
you can:

```
Use emerging-market-review on this PR. Target market is Kenya, tier C Android.
```

### Without the plugin system

Clone and symlink into your project, or copy the directories you want:

```bash
git clone https://github.com/Kaguara/emerging-market-skills.git
ln -s "$(pwd)/emerging-market-skills/skills" .claude/skills
```

Per-project skills live in `.claude/skills/`; skills you want everywhere go in
`~/.claude/skills/`.

## claude.ai

Download `bundle.zip` from the [latest release][releases] and upload it in
Settings → Capabilities → Skills. The bundle contains only `skills/`, which is
all the web app needs.

## Cursor

Cursor reads rules from `.cursor/rules/`. The skills are plain markdown, so:

```bash
mkdir -p .cursor/rules
for skill in emerging-market-skills/skills/*/; do
  cp "$skill/SKILL.md" ".cursor/rules/$(basename "$skill").mdc"
done
```

Cursor's frontmatter uses `description` and `globs`. The `description` field
carries over as-is; add `alwaysApply: false` so rules load contextually rather
than on every request, which is the behaviour these are written for.

## GitHub Copilot

Copilot reads repository-wide instructions from
`.github/copilot-instructions.md`. It does not support per-skill loading, so
concatenating all nine would blow the context. Copy in the one or two skills
that match what you are building, or paste the rules tables — the rules survive
compression better than the prose does.

## Any tool with a system prompt

Concatenate the skills you want and prepend them. Keep the frontmatter; the
`description` fields are what let a model decide which skill applies.

```bash
cat skills/network-resilience/SKILL.md skills/payload-budgets/SKILL.md > context.md
```

For an agent with tool access, mounting the repo and letting it read
`skills/*/rules.yml` directly works better than pasting prose — the rules are
structured, and the model can cite IDs back to you.

## Using the validators

The audit scripts run against your codebase, not against this repo:

```bash
pip install -r requirements.txt
python3 skills/payload-budgets/scripts/audit_budget.py ~/code/my-app
```

They are deliberately conservative and will miss things. They find structure;
the device finds the truth. Every skill's Verification section says what to
measure once the static checks pass.

## Verifying you have the right thing

```bash
python3 tools/validate_skills.py
```

Should report every skill passing. If it does not, you have a partial copy.

[releases]: https://github.com/Kaguara/emerging-market-skills/releases/latest
