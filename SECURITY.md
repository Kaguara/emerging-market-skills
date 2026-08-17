# Security

## What this repo is

Markdown instructions, YAML rule files, and a handful of Python and JavaScript
audit scripts. There is no service, no runtime, and no user data. The realistic
risk surface is small but not empty.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository
(**Security → Report a vulnerability**), or email **akaguara@gmail.com**.

Please do not open a public issue for a security report. You will get an
acknowledgement within seven days.

## What counts

- **Malicious content in a skill.** These files are read by AI agents that may
  have tool access. A pull request that adds instructions attempting to exfiltrate
  data, weaken a security control, or manipulate an agent into acting outside the
  user's intent is a security issue, and the most plausible attack on this repo.
- **Unsafe validator scripts.** The scripts in `tools/` and `skills/*/scripts/`
  run against contributors' codebases on their machines and in their CI. Anything
  that executes untrusted input, writes outside its working directory, or makes
  unexpected network calls is a vulnerability.
- **Dependency issues** in `requirements.txt`.

## What does not count

A rule you disagree with, or one that gives poor engineering advice, is a
correctness issue rather than a security one. Open a normal issue — the
`field-report` template is built for exactly that.

## For people using these skills

Skills are instructions to an AI agent, and agents in this project's target
audience frequently have file and shell access. Read what you install, pin to a
release tag rather than tracking `main`, and review diffs when you update — the
same discipline you would apply to any dependency that executes in your
environment.
