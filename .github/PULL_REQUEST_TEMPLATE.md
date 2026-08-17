# What this changes

<!-- One or two sentences. If it closes an issue, link it. -->

## Checklist

- [ ] `python3 tools/validate_skills.py` passes locally
- [ ] If I changed `rules.yml`, I updated the rules table in `SKILL.md` to match
- [ ] If I added a `published` or `vendor` citation, it has a `###` entry in `docs/SOURCES.md`
- [ ] I did not paste text from a source; I paraphrased and cited it

## For new or changed rules

Delete this section if the PR does not touch a rule.

| | |
|---|---|
| **Rule ID** | |
| **Market** | <!-- Country or region. "Emerging markets" is not a market. --> |
| **Device / network tier** | <!-- A, B, C, or D — see docs/EVIDENCE.md --> |
| **Observed effect** | <!-- What changed, and how it was measured --> |
| **Evidence tier** | <!-- field / published / vendor --> |

Rules at `critical` need evidence. If you believe a rule is critical but cannot
source it, set `warning` and leave a `TODO` naming the evidence that would
promote it — that is the honest outcome, not a failed contribution.

## Anything you are unsure about

<!-- Genuinely useful. Reviewers would rather know where you hesitated. -->
