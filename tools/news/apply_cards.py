"""Apply verified card proposals to the site (stage 2 helper, used by /aurora-news).

Usage: python apply_cards.py proposed_cards.json [--repo PATH]

proposed_cards.json:
  {"new":   [{"arxiv", "date": "YYYY-MM", "person", "title", "blurb",
              "figure": "/news/<slug>.jpg", "figure_src": "/abs/path/to/crop.jpg",
              "venue": optional, "survey": optional "VENUS"|"MINERVA"}, ...],   # in display order
   "fixes": {"<arxiv id>": {"title"|"blurb"|"venue"|"person": value}},
   "orcid_fixes": {"<member name>": "<orcid>"}}

New cards go to the top of their month block, in the order given (put member
first-author cards first). Existing cards are never reordered. A card whose arXiv id is
already listed is refused.
"""
import argparse
import json
import re
import shutil
from pathlib import Path

DEFAULT_REPO = Path.home() / "Library/CloudStorage/Dropbox/_claude_code/aurora_institute_website"
KEY_ORDER = ["type", "date", "person", "venue", "survey", "title", "blurb", "url", "figure"]


def aid(item):
    m = re.search(r"arXiv:([0-9]{4}\.[0-9]{4,5})", item.get("url", ""))
    return m.group(1) if m else None


def card(c):
    out = {"type": "paper", "date": c["date"], "person": c["person"]}
    if c.get("venue"):
        out["venue"] = c["venue"]
    if c.get("survey"):
        out["survey"] = c["survey"]
    out.update({"title": c["title"], "blurb": c["blurb"],
                "url": f"https://ui.adsabs.harvard.edu/abs/arXiv:{c['arxiv']}/abstract", "figure": c["figure"]})
    return out


def ordered(item):
    return {k: item[k] for k in KEY_ORDER if k in item} | {k: v for k, v in item.items() if k not in KEY_ORDER}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proposal")
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    a = ap.parse_args()
    repo = Path(a.repo)
    P = json.loads(Path(a.proposal).read_text())
    news_p = repo / "site/src/data/news.json"
    news = json.loads(news_p.read_text())
    items = news["items"]
    listed = {aid(it) for it in items}

    # validate everything before touching any file
    seen_new = set()
    for c in P.get("new", []):
        if c["arxiv"] in listed or c["arxiv"] in seen_new:
            raise SystemExit(f"arXiv:{c['arxiv']} is already listed or appears twice in the proposal")
        seen_new.add(c["arxiv"])
        if not re.fullmatch(r"\d{4}-\d{2}", c["date"]):
            raise SystemExit(f"bad date {c['date']} for {c['arxiv']}")
        src, dst = Path(c["figure_src"]), repo / "site/public" / c["figure"].lstrip("/")
        if not src.exists():
            raise SystemExit(f"figure not found: {src}")
        if dst.exists() and dst.read_bytes() != src.read_bytes():
            raise SystemExit(f"{dst} already exists with different content; choose another file name")
    unknown = set(P.get("fixes", {})) - listed - seen_new
    if unknown:
        raise SystemExit(f"fixes for cards that are not on the site: {sorted(unknown)}")

    added = 0
    for c in reversed(P.get("new", [])):  # reversed + insert-at-top keeps the given order
        idx = next((i for i, it in enumerate(items) if it["date"] <= c["date"]), len(items))
        items.insert(idx, card(c))
        dst = repo / "site/public" / c["figure"].lstrip("/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(c["figure_src"]), dst)
        added += 1

    fixed = 0
    for it in items:
        fx = P.get("fixes", {}).get(aid(it))
        if fx:
            it.update(fx)
            fixed += 1
    news["items"] = [ordered(it) for it in items]
    news_p.write_text(json.dumps(news, indent=2, ensure_ascii=False) + "\n")

    if P.get("orcid_fixes"):
        team_p = repo / "site/src/data/team.json"
        team = json.loads(team_p.read_text())
        for t in team["tiers"]:
            for m in t.get("members", []):
                if m["name"] in P["orcid_fixes"]:
                    m["orcid"] = P["orcid_fixes"][m["name"]]
        team_p.write_text(json.dumps(team, indent=2, ensure_ascii=False) + "\n")

    print(f"added {added} cards, fixed {fixed} cards, orcid fixes {len(P.get('orcid_fixes', {}))}; news items now {len(items)}")


if __name__ == "__main__":
    main()
