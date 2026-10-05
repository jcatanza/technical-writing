# Handoff

State on 2026-10-05: the skill is complete, installed by symlink, and its tests pass. `examples/` holds eleven seed pairs with neutral subject matter. `examples-local/` does not exist yet, because the reader has recorded no pair of their own.

To resume:

1. Run `./install.sh` if `~/.claude/skills/technical-writing` is missing.
2. Run `python3 -m pytest -q`.
3. New pairs arrive through `scripts/add_example.py` and land in `examples-local/`. Git ignores them, so they never need a commit.

Open items:

- The checker does not separate answers the reader flagged from answers they did not (README, section "The checker"). The faults the reader flags most, undefined words and abstract openings, are not mechanical.
- The learned-label check matches labels of two or more words only. A one-word label such as "support" would match ordinary prose.
- The repository has no license file. The owner chooses the license.
