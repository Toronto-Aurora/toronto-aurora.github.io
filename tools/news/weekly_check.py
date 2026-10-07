"""Weekly check for the Aurora "Recent papers" list (stage 1 of the news automation).

Runs from launchd every Monday 07:30 Toronto time. Deterministic, no LLM:
  1. read team.json and news.json from the public repo (raw.githubusercontent.com)
  2. search arXiv for member first/second-author papers and VENUS/MINERVA papers in
     [last successful run - 35 days, today] (sweep.py, two routes)
  3. drop papers already listed or already judged (state.json)
  4. audit the existing cards: title vs arXiv, venue now published (arXiv journal_ref,
     Crossref), card person is a member and author 1/2 or the survey lead, ORCIDs resolve
     to the member, papers judged "include" that never reached the site
  5. write candidates_latest.json and report.txt next to the state file; e-mail the owner
     (self only) when there are candidates, NEW audit findings, errors, or a crash
Judging candidates and editing the site is stage 2, the /aurora-news skill.

Local settings (not in this public repo): ~/.local/share/aurora_news/config.json with
  {"self_email": ..., "graph_cache": <path to the MSAL token cache>, "graph_client_id": ...,
   "graph_authority": ..., "graph_scopes": [...]}

Options: --no-email, --dry-run (do not update state), --start/--end YYYY-MM-DD (a manual
window never moves last_run), --state PATH (outputs and the lock go to its directory),
--test-email (send a one-line test mail and exit)
"""
import argparse
import datetime as dt
import difflib
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sweep as sw  # noqa: E402

HOME = Path.home()
STATE_DIR = HOME / ".local/share/aurora_news"
CONFIG = STATE_DIR / "config.json"
RAW = "https://raw.githubusercontent.com/Toronto-Aurora/toronto-aurora.github.io/main/site/src/data/"
UA = sw.UA
LOOKBACK_DAYS = 35  # arXiv can hold a submission for weeks before announcing it
SURVEY_LEAD = {"VENUS": "Seiji Fujimoto", "MINERVA": "Adam Muzzin"}
JOURNALS = {
    "the astrophysical journal": "ApJ", "the astrophysical journal letters": "ApJL",
    "the astrophysical journal supplement series": "ApJS", "the astronomical journal": "AJ",
    "astronomy & astrophysics": "A&A", "astronomy and astrophysics": "A&A",
    "monthly notices of the royal astronomical society": "MNRAS", "nature": "Nature",
    "nature astronomy": "Nat. Astron.", "journal of cosmology and astroparticle physics": "JCAP",
    "the open journal of astrophysics": "OJAp", "publications of the astronomical society of the pacific": "PASP",
    "physical review d": "PRD", "physical review letters": "PRL",
}


def log(msg):
    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def write_json_atomic(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    os.replace(tmp, path)


def fetch_json(url):
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            log(f"  ! {url[:90]}: {e}")
            time.sleep(20 * (k + 1))
    raise RuntimeError(f"could not fetch {url}")


def nt(s):
    """Normalize a title for comparison: drop LaTeX commands, $, HTML entities, accents, punctuation."""
    s = html.unescape(s or "")
    s = re.sub(r"\\[a-zA-Z]+", " ", s).replace("$", " ")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def arxiv_id(item):
    m = re.search(r"arXiv:([0-9]{4}\.[0-9]{4,5})", item.get("url", ""))
    return m.group(1) if m else None


def fhash(f):
    return hashlib.sha1(f"{f['kind']}|{f.get('arxiv')}|{f['detail']}".encode()).hexdigest()[:12]


def load_state(path):
    if path.exists():
        return json.loads(path.read_text())
    return {"last_run": None, "judged": {}, "pending": {}, "audit_ack": {}}


def acked(state, key, kind, finding):
    a = state.get("audit_ack", {}).get(key or "", {}).get(kind)
    if a is None:
        return False
    if isinstance(a, str):  # old format: permanent
        return True
    return a.get("detail_hash") in (None, fhash(finding))


# --------------------------------------------------------------------------- audit

def audit(items, members, state):
    """Findings about the existing paper cards (acknowledged ones are skipped)."""
    findings = []
    papers = [it for it in items if it.get("type", "paper") == "paper"]
    ids = [arxiv_id(it) for it in papers]
    meta = {}
    chunk_ids = [i for i in ids if i]
    for k in range(0, len(chunk_ids), 50):
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": ",".join(chunk_ids[k:k + 50]), "max_results": 60})
        for en in sw.parse_api(sw.get(url, log=log)):
            meta[en["arxiv"]] = en
        time.sleep(4)
    table = sw.member_table(members)

    def add(aid, kind, detail):
        f = {"arxiv": aid, "kind": kind, "detail": detail}
        if not acked(state, aid, kind, f):
            findings.append(f)

    for it, aid in zip(papers, ids):
        m = meta.get(aid)
        if not aid or not m:
            add(aid, "missing", "arXiv record not found for card: " + it.get("title", "")[:80])
            continue
        a, c = nt(m["title"]), nt(it["title"])
        if not (a.startswith(c) or difflib.SequenceMatcher(None, a, c).ratio() > 0.9):
            add(aid, "title", f"card: {it['title']} | arXiv: {m['title']}")
        person = it.get("person", "")
        survey_ok = it.get("survey") and SURVEY_LEAD.get(it["survey"]) == person
        if person not in table and not survey_ok:
            add(aid, "not_member", f"card person {person} is not in team.json (authors 1-2: {', '.join(m['authors'][:2])})")
        elif person in table and not survey_ok:
            top2 = [i + 1 for i, au in enumerate(m["authors"][:2]) if sw.classify(au, person, table) in ("match", "initial")]
            if not top2:
                add(aid, "person", f"{person} is not author 1/2 ({', '.join(m['authors'][:2])}) and the card is not a survey card")
        if not it.get("venue"):
            hint = venue_hint(m)
            if hint:
                add(aid, "venue", hint)
    return findings


def venue_hint(m):
    if m.get("journal_ref"):
        return f"arXiv journal_ref: {m['journal_ref']}" + (f" (doi {m['doi']})" if m.get("doi") else "")
    if m.get("doi"):
        return f"arXiv doi: {m['doi']}"
    first = (sw.norm(m["authors"][0]) or [""])[-1] if m["authors"] else ""
    q = {"query.bibliographic": m["title"][:250], "rows": 5, "filter": f"from-pub-date:{m['v1']}",
         "select": "DOI,title,container-title,type,author,published,publisher"}
    try:
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(q)
        items = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))["message"]["items"]
    except Exception as e:
        log(f"  ! crossref: {e}")
        return None
    finally:
        time.sleep(1)
    for c in items:
        if c.get("type") not in ("journal-article", "proceedings-article"):
            continue
        t = (c.get("title") or [""])[0]
        fam = (c.get("author") or [{}])[0].get("family", "")
        if difflib.SequenceMatcher(None, nt(t), nt(m["title"])).ratio() > 0.9 and sw.norm(fam)[-1:] == [first]:
            cont = (c.get("container-title") or [""])[0]
            abbr = JOURNALS.get(html.unescape(cont).lower(), "Proc. SPIE" if "SPIE" in (c.get("publisher") or "") else cont)
            pub = "-".join(str(x) for x in (c.get("published") or {}).get("date-parts", [[None]])[0] if x)
            return f"Crossref: {abbr} ({c['DOI']}, published {pub})"
    return None


def orcid_check(team, state):
    findings = []
    for t in team["tiers"]:
        for mbr in t.get("members", []):
            oid = mbr.get("orcid")
            if not oid:
                continue
            req = urllib.request.Request(f"https://pub.orcid.org/v3.0/{oid}/person", headers={"Accept": "application/json", **UA})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=30))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    f = {"arxiv": None, "kind": "orcid", "detail": f"{mbr['name']}: {oid} does not exist (404)"}
                    if not acked(state, "orcid:" + mbr["name"], "orcid", f):
                        findings.append(f)
                    continue
                raise
            n = d.get("name") or {}
            fam = ((n.get("family-name") or {}).get("value") or "")
            credit = ((n.get("credit-name") or {}).get("value") or "")
            if sw.norm(mbr["name"].split()[-1])[-1] not in sw.norm(fam + " " + credit):
                f = {"arxiv": None, "kind": "orcid",
                     "detail": f"{mbr['name']}: {oid} resolves to '{(n.get('given-names') or {}).get('value', '')} {fam}'".strip()}
                if not acked(state, "orcid:" + mbr["name"], "orcid", f):
                    findings.append(f)
            time.sleep(0.3)
    return findings


# --------------------------------------------------------------------------- email

def graph_token(cfg):
    """Silent token only. Never fall back to the device-code flow: nobody is there to answer it."""
    import msal
    cache_path = Path(cfg["graph_cache"])
    cache = msal.SerializableTokenCache()
    cache.deserialize(cache_path.read_text())
    app = msal.PublicClientApplication(cfg["graph_client_id"], authority=cfg["graph_authority"], token_cache=cache)
    accounts = app.get_accounts()
    acct = next((a for a in accounts if cfg["self_email"].lower() in a.get("username", "").lower()), accounts[0] if accounts else None)
    res = app.acquire_token_silent(cfg["graph_scopes"], account=acct) if acct else None
    if not res or "access_token" not in res:
        raise RuntimeError("silent Graph token failed; refresh it interactively (email_drafter/graph_auth.py)")
    if cache.has_state_changed:
        try:  # other jobs share this cache, so write it atomically and never let a write failure stop the mail
            tmp = cache_path.with_name(cache_path.name + ".aurora.tmp")
            tmp.write_text(cache.serialize())
            os.replace(tmp, cache_path)
        except Exception as e:
            log(f"  ! could not save the refreshed token cache: {e}")
    return res["access_token"]


def send_self_email(subject, body, out_dir):
    try:
        cfg = json.loads(CONFIG.read_text())
        tok = graph_token(cfg)
        payload = json.dumps({"message": {"subject": subject, "body": {"contentType": "Text", "content": body},
                                          "toRecipients": [{"emailAddress": {"address": cfg["self_email"]}}]},
                              "saveToSentItems": "false"}).encode()
        req = urllib.request.Request("https://graph.microsoft.com/v1.0/me/sendMail", data=payload, method="POST",
                                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status != 202:
                raise RuntimeError(f"Graph sendMail HTTP {r.status}")
        log(f"emailed: {subject}")
        (out_dir / "NOTIFY_FAILED").unlink(missing_ok=True)
        return True
    except Exception as e:
        log(f"! email failed: {e}")
        (out_dir / "NOTIFY_FAILED").write_text(f"{dt.datetime.now().isoformat(timespec='seconds')}\t{subject}\t{e}\n")
        (out_dir / "pending_email.txt").write_text(subject + "\n\n" + body)
        try:
            subprocess.run(["osascript", "-e", f'display notification "メール送信に失敗。{out_dir}/pending_email.txt を参照" with title "Aurora news"'], timeout=10)
        except Exception:
            pass
        return False


# --------------------------------------------------------------------------- main

def take_lock(lock):
    if lock.exists():
        try:
            pid = int(lock.read_text().strip() or 0)
            os.kill(pid, 0)
            return False  # a live run holds it
        except (ValueError, ProcessLookupError):
            log(f"removing stale lock {lock}")
        except PermissionError:
            return False
    lock.write_text(str(os.getpid()))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-email", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--state", default=str(STATE_DIR / "state.json"))
    ap.add_argument("--test-email", action="store_true")
    args = ap.parse_args()
    out_dir = Path(args.state).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.test_email:
        ok = send_self_email("[Aurora news] テスト送信", "週次チェックのメール経路のテストです。返信は不要です。", out_dir)
        sys.exit(0 if ok else 1)

    lock = out_dir / "run.lock"
    if not take_lock(lock):
        log(f"another run (pid {lock.read_text().strip()}) holds {lock}; exiting")
        return
    try:
        run(args, out_dir)
    except Exception:
        tb = traceback.format_exc()
        log(tb)
        (out_dir / "last_crash.txt").write_text(f"{dt.datetime.now().isoformat(timespec='seconds')}\n{tb}")
        if not args.no_email:
            send_self_email(f"[Aurora news] 週次チェックが異常終了（{dt.date.today().isoformat()}）",
                            "週次チェックが途中で止まりました。今週の候補は出ていません。\n\n" + tb[-3000:], out_dir)
        raise
    finally:
        if lock.exists() and lock.read_text().strip() == str(os.getpid()):
            lock.unlink()


def run(args, out_dir):
    state_path = Path(args.state).resolve()
    state = load_state(state_path)
    today = dt.date.today()
    manual = bool(args.start or args.end)
    end = args.end or today.isoformat()
    if args.start:
        start = args.start
    else:
        base = dt.date.fromisoformat(state["last_run"]) if state.get("last_run") else today
        start = (base - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    log(f"window {start} .. {end}{' (manual)' if manual else ''}")

    team = fetch_json(RAW + "team.json")
    news = fetch_json(RAW + "news.json")
    members = [m["name"] for t in team["tiers"] for m in t.get("members", [])]
    listed = {arxiv_id(it) for it in news["items"]}

    res = sw.sweep(members, start, end, log=log)
    errors = list(res["errors"])
    judged = state.get("judged", {})
    new = {}
    for member, rec in res["members"].items():
        for aid, h in rec["hits"].items():
            if aid in listed or aid in judged:
                continue
            c = new.setdefault(aid, {"arxiv": aid, "title": h["title"], "v1": h.get("v1"), "category": h.get("category"),
                                     "journal_ref": h.get("journal_ref"), "doi": h.get("doi"), "flags": []})
            c["flags"].append({"member": member, "position": h["position"], "name_as_listed": h["name_as_listed"],
                               "match": h["match"], "routes": h["routes"]})
    survey = {aid: s for aid, s in res["survey"].items() if aid not in listed and aid not in judged and aid not in new}

    findings = []
    try:
        findings += audit(news["items"], members, state)
    except sw.ArxivUnavailable:
        raise
    except Exception as e:
        errors.append({"stage": "audit", "error": str(e)[:300]})
    try:
        findings += orcid_check(team, state)
    except Exception as e:
        errors.append({"stage": "orcid", "error": str(e)[:300]})
    for aid, j in judged.items():
        if j.get("decision") == "include" and aid not in listed and j.get("date", today.isoformat()) <= (today - dt.timedelta(days=7)).isoformat():
            f = {"arxiv": aid, "kind": "unlisted_include", "detail": f"judged include on {j.get('date')} but not on the site ({j.get('reason', '')[:80]})"}
            if not acked(state, aid, "unlisted_include", f):
                findings.append(f)

    seen = state.get("findings_seen", {})
    for f in findings:
        f["hash"] = fhash(f)
        f["new"] = f["hash"] not in seen
    new_findings = [f for f in findings if f["new"]]

    pending = state.get("pending", {})
    carried = {aid: p for aid, p in pending.items() if aid not in new and aid not in survey and aid not in judged and aid not in listed}
    for aid, c in new.items():
        c["first_seen"] = pending.get(aid, {}).get("first_seen", today.isoformat())
    for aid, s in survey.items():
        s["first_seen"] = pending.get(aid, {}).get("first_seen", today.isoformat())

    out = {"generated": dt.datetime.now().isoformat(timespec="seconds"), "window": [start, end], "manual_window": manual,
           "new_member_papers": list(new.values()), "survey_papers": list(survey.values()),
           "carried_over": [{"arxiv": aid, **p} for aid, p in carried.items()], "audit": findings, "errors": errors,
           "counts": {m: {"api": r["api_n"], "web": r["web_n"], "hits": len(r["hits"]), "rejected_forms": r["rejected_forms"]}
                      for m, r in res["members"].items()}}
    write_json_atomic(out_dir / "candidates_latest.json", out)
    write_json_atomic(out_dir / f"candidates_{today.isoformat()}.json", out)
    report = render(out)
    (out_dir / "report.txt").write_text(report)
    print(report, flush=True)

    last_rem = state.get("last_carried_reminder")
    remind_carried = bool(carried) and (not last_rem or last_rem <= (today - dt.timedelta(days=28)).isoformat())
    actionable = bool(new or survey or new_findings or errors or remind_carried)
    if actionable and not args.no_email:
        subj = (f"[Aurora news] 候補 {len(new) + len(survey)} 件" + (f"・持ち越し {len(carried)} 件" if carried else "")
                + f"・点検 {len(findings)} 件（新規 {len(new_findings)}）" + ("・一部失敗" if errors else "") + f"（{today.isoformat()}）")
        send_self_email(subj, report, out_dir)
    elif not actionable:
        log("nothing new to act on; no email")

    if not args.dry_run:
        disk = load_state(state_path)  # re-read: state_tool may have recorded decisions during this run
        fresh_judged = disk.get("judged", {})
        if not manual and not errors:
            disk["last_run"] = max(disk.get("last_run") or end, end)
        disk["pending"] = {aid: p for aid, p in {
            **{aid: {"title": c["title"], "first_seen": c["first_seen"], "kind": "member"} for aid, c in new.items()},
            **{aid: {"title": s["title"], "first_seen": s["first_seen"], "kind": "survey"} for aid, s in survey.items()},
            **carried}.items() if aid not in fresh_judged}
        disk["findings_seen"] = {f["hash"]: seen.get(f["hash"], today.isoformat()) for f in findings}
        if remind_carried and not args.no_email:
            disk["last_carried_reminder"] = today.isoformat()
        disk["last_status"] = {"time": out["generated"], "errors": len(errors), "new": len(new), "survey": len(survey),
                               "findings": len(findings), "window": [start, end]}
        write_json_atomic(state_path, disk)


def render(out):
    L = [f"Aurora サイト Recent papers の週次チェック（{out['generated'][:10]}、検索窓 {out['window'][0]}〜{out['window'][1]}）", ""]
    if out["new_member_papers"]:
        L.append(f"【新しい候補】メンバーが第1・第2著者（名前の一致のみで未検証）: {len(out['new_member_papers'])} 件")
        for c in out["new_member_papers"]:
            fl = "; ".join(f"{f['member']} 第{f['position']}著者（{f['name_as_listed']}、{'名前一致' if f['match'] == 'match' else '頭文字のみ'}）" for f in c["flags"])
            L.append(f"  - arXiv:{c['arxiv']}  {c.get('v1') or ''}  {fl}\n      {c['title']}")
        L.append("")
    if out["survey_papers"]:
        L.append(f"【VENUS/MINERVA の論文かもしれないもの】 {len(out['survey_papers'])} 件")
        for s in out["survey_papers"]:
            L.append(f"  - arXiv:{s['arxiv']}  {s.get('v1') or ''}  {(s.get('authors') or ['?'])[0]} ほか\n      {s['title']}")
        L.append("")
    if out["carried_over"]:
        L.append(f"【前回からの持ち越し（未判定）】 {len(out['carried_over'])} 件")
        for p in out["carried_over"]:
            L.append(f"  - arXiv:{p['arxiv']}  {p.get('title', '')[:100]}（初出 {p.get('first_seen')}）")
        L.append("")
    if out["audit"]:
        L.append(f"【既存カードと team.json の点検】 {len(out['audit'])} 件（うち新規 {sum(f['new'] for f in out['audit'])} 件）")
        for f in out["audit"]:
            L.append(f"  - {'[新規]' if f['new'] else '[既報]'} [{f['kind']}] {('arXiv:' + f['arxiv']) if f.get('arxiv') else ''}  {f['detail']}")
        L.append("")
    if out["errors"]:
        L.append("【検索・点検の一部が失敗（この部分は見ていない。次回の窓でもう一度見る）】")
        for e in out["errors"]:
            L.append(f"  - {e}")
        L.append("")
    if len(L) == 2:
        L.append("新しい候補・点検項目はありません。")
    L += ["次の一手: Claude Code のセッションで /aurora-news を実行すると、一次資料での照合からカード案の作成まで進めます（公開は push の OK 後）。",
          f"候補ファイル: {STATE_DIR}/candidates_latest.json"]
    return "\n".join(L)


if __name__ == "__main__":
    main()
