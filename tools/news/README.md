# tools/news: weekly check for the "Recent papers" page

Stage 1 runs every Monday 07:30 (Toronto) from launchd and needs no LLM. It searches
arXiv for papers where a member listed in `site/src/data/team.json` is first or second
author, plus possible VENUS/MINERVA survey papers. It skips papers already in
`site/src/data/news.json` or already judged, audits the existing cards, and e-mails the
site owner when something needs a decision. Stage 2 is the Claude Code skill
`/aurora-news`, which verifies candidates against the papers, drafts the cards and
figures, and leaves a local commit for review.

| file | role |
|---|---|
| `sweep.py` | arXiv search: export API by surname plus the arxiv.org web search by full name, names matched locally |
| `weekly_check.py` | stage 1: window, dedup against `state.json`, card audit (title, venue, person, ORCID), report, e-mail |
| `apply_cards.py` | stage 2 helper: add verified cards, apply fixes, copy figures |
| `state_tool.py` | record decisions (`judge`, `ack`) so the same papers are not flagged again |
| `com.sfseiji.aurora-news-weekly.plist`, `deploy.sh` | launchd job; `bash tools/news/deploy.sh` copies the scripts to `~/.local/share/aurora_news/` and reloads the job |

When a new member's arXiv name differs from the website name (nickname, middle name),
add it to `NICKNAMES` in `sweep.py` and redeploy.

The e-mail address and the Microsoft Graph token-cache location live in
`~/.local/share/aurora_news/config.json` on the machine that runs the job, not in this
repository. The job e-mails only when there are candidates, new audit findings, search
errors, or a crash; a failed send leaves `NOTIFY_FAILED` and `pending_email.txt` next to
the state file.

Trial runs: give them their own state file, because the outputs and the lock are written
next to it (a run takes about 8 minutes):

```
mkdir -p /tmp/aurora_trial && cp ~/.local/share/aurora_news/state.json /tmp/aurora_trial/
python3 ~/.local/share/aurora_news/weekly_check.py --no-email --dry-run --state /tmp/aurora_trial/state.json --start 2026-09-01 --end 2026-09-30
```
