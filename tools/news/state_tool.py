"""Record decisions in the weekly-check state so the same papers are not re-flagged.

  python state_tool.py judge <arxiv> include|exclude "<reason>"
      record "include" only after the card is on the live site (a declined push would
      otherwise hide the paper; the weekly audit reports include-but-unlisted after 7 days)
  python state_tool.py ack <arxiv | "orcid:<member name>"> <kind> "<reason>"
      silence one audit finding; kinds: title person not_member venue missing orcid unlisted_include.
      The finding's current text is stored, so a changed finding (e.g. a new venue hint) is reported again.
  python state_tool.py show
Options: --state PATH (default ~/.local/share/aurora_news/state.json)
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

DEFAULT = Path.home() / ".local/share/aurora_news/state.json"
KINDS = ("title", "person", "not_member", "venue", "missing", "orcid", "unlisted_include")


def norm_id(s):
    if s.startswith("orcid:"):
        return s
    m = re.search(r"(\d{4}\.\d{4,5})", s)
    if not m:
        raise SystemExit(f"not an arXiv id: {s}")
    return m.group(1)


def load(p):
    return json.loads(p.read_text()) if p.exists() else {"last_run": None, "judged": {}, "pending": {}, "audit_ack": {}}


def save(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False))
    os.replace(tmp, p)


def current_finding(state_path, key, kind):
    """The matching finding in candidates_latest.json next to the state file, if any."""
    c = state_path.parent / "candidates_latest.json"
    if not c.exists():
        return None
    for f in json.loads(c.read_text()).get("audit", []):
        fkey = f.get("arxiv") or ("orcid:" + f["detail"].split(":")[0] if f["kind"] == "orcid" else None)
        if fkey == key and f["kind"] == kind:
            return f
    return None


def main():
    argv = sys.argv[1:]
    p = DEFAULT
    if "--state" in argv:
        i = argv.index("--state")
        p = Path(argv[i + 1]).expanduser()
        argv = argv[:i] + argv[i + 2:]
    cmd = argv[0] if argv else "show"
    s = load(p)
    today = dt.date.today().isoformat()
    if cmd == "judge":
        aid, decision, reason = norm_id(argv[1]), argv[2], argv[3]
        if decision not in ("include", "exclude"):
            raise SystemExit("decision must be include or exclude")
        s["judged"][aid] = {"decision": decision, "reason": reason, "date": today}
        s.get("pending", {}).pop(aid, None)
    elif cmd == "ack":
        key, kind, reason = norm_id(argv[1]), argv[2], argv[3]
        if kind not in KINDS:
            raise SystemExit(f"kind must be one of {KINDS}")
        f = current_finding(p, key, kind)
        h = hashlib.sha1(f"{f['kind']}|{f.get('arxiv')}|{f['detail']}".encode()).hexdigest()[:12] if f else None
        s.setdefault("audit_ack", {}).setdefault(key, {})[kind] = {"reason": reason, "date": today, "detail_hash": h,
                                                                   "detail": f["detail"] if f else None}
        if not f:
            print("note: no matching finding in candidates_latest.json; the ack applies to any future text")
    elif cmd == "show":
        st = s.get("last_status", {})
        print(f"last_run {s.get('last_run')}  last_status {st}")
        print(f"judged {len(s.get('judged', {}))}  pending {len(s.get('pending', {}))}  acks {sum(len(v) for v in s.get('audit_ack', {}).values())}")
        for aid, q in s.get("pending", {}).items():
            print("pending", aid, q.get("kind"), q.get("first_seen"), q.get("title", "")[:80])
        return
    else:
        raise SystemExit(__doc__)
    save(p, s)
    print("ok", cmd, argv[1:3])


if __name__ == "__main__":
    main()
