"""Find arXiv papers where an Aurora member is first or second author, plus possible
VENUS / MINERVA survey papers, inside a date window. Deterministic, no LLM.
Graduate students (the "students" tier of team.json) count only as first author, and
only when one of their supervisors is also on the author list (student_supervisors()).

Two independent routes, because each one misses papers the other finds:
  A. arXiv export API by surname only. Server-side name matching is unreliable:
     au:Surname_I misses authors listed with a spelled-out first name, au:Surname_First
     misses members whose arXiv name differs from team.json, and au:Antwi_Danso returns
     nothing (hyphenated surnames must be quoted: au:"Antwi-Danso"). Common surnames are
     restricted to astro-ph.
  B. arxiv.org advanced web search (a different backend): full-name author queries for
     every accepted given-name variant, plus the bare surname when it is hyphenated.
Names are matched locally (classify()). A route that fails is reported in "errors";
an empty answer is only trusted when the server says so.

Library use: sweep(members, start, end, students=...) -> dict. CLI: python sweep.py START END [out.json]
"""
import datetime as dt
import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

UA = {"User-Agent": "aurora-news-sweep/1.1 (+https://toronto-aurora.github.io)"}

# arXiv given-name variants that differ from team.json, and canonical middle initials.
# Add new members here when their arXiv name differs from the website name.
NICKNAMES = {
    "Josh Speagle": ["josh", "joshua"],
    "Will McClymont": ["will", "william"],
    "Norman Murray": ["norman", "norm"],
    "Gwendolyn Eadie": ["gwendolyn", "gwen"],
    "Roberto Abraham": ["roberto", "bob"],
    "Yoshihisa Asada": ["yoshihisa", "yoshi"],
    "Ue-Li Pen": ["ueli", "ue"],
    "J. Richard Bond": ["richard", "dick"],
    "Jose Maria Palencia": ["jose", "josemaria"],
    "Lily Han Zhang": ["lily", "han"],
}
FIRST_INITIAL = {"J. Richard Bond": "j"}  # publishes as "J. R. Bond"
MIDDLE = {"Ting Li": "s", "Josh Speagle": "s", "Jonah Gannon": "s", "Chloe Cheng": "m", "Gwendolyn Eadie": "m"}
COMMON = {"Zhang", "Li", "Nguyen", "Cheng", "Martin", "Cho", "Bond", "Pen", "Fei", "Murray", "Abraham", "Guo",
          "Edward", "Myers",
          "Wang", "Chen", "Liu", "Yang", "Wu", "Huang", "Zhao", "Zhou", "Xu", "Sun", "Lin", "Kim", "Lee",
          "Park", "Smith", "Brown", "Jones", "Sato", "Suzuki", "Tanaka", "Singh", "Kumar", "Garcia", "Lopez"}
ASTRO = "(cat:astro-ph.GA OR cat:astro-ph.CO OR cat:astro-ph.HE OR cat:astro-ph.IM OR cat:astro-ph.SR OR cat:astro-ph.EP)"
SURVEY_WORD = re.compile(r"\b(VENUS|MINERVA)\b(?!-Australis)")  # upper case only: the planet is "Venus";
# MINERVA-Australis is an exoplanet telescope. Survey papers are JWST papers, so also require JWST:
JWST_WORD = re.compile(r"JWST|James Webb|NIRCam|NIRSpec|\bMIRI\b")
SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}
TITLES = re.compile(r"^(prof(essor)?|dr)\.?\s+", re.I)
DASHES = re.compile("[‐-―−]")
MAX_ENTRIES = 5000


class ArxivUnavailable(RuntimeError):
    """Several consecutive URLs failed completely: stop instead of waiting for hours."""


def norm(s):
    s = DASHES.sub(" ", html.unescape(s))
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    toks = re.sub(r"[^a-z ]", " ", s.replace("-", " ")).split()
    return [t for t in toks if t not in SUFFIXES] or toks


def member_table(names):
    """team.json display names -> {name: (surname, [given variants])}."""
    out = {}
    for name in names:
        parts = [p for p in name.replace(".", "").split() if p.lower() not in SUFFIXES]
        if not parts:
            continue
        surname = parts[-1]
        given = [p for p in parts[:-1] if len(p) > 1] or parts[:-1]
        variants = NICKNAMES.get(name, [norm(given[0])[0]] if given else [""])
        out[name] = (surname, variants)
    return out


def student_supervisors(team):
    """{student name: [supervisor names]} from the "students" tier. The field may be a string
    ("A and B", "A, B & C", "A; B", "A/B") or a list; titles and notes in parentheses are dropped."""
    out = {}
    for t in team["tiers"]:
        if t.get("id") != "students":
            continue
        for m in t.get("members", []):
            raw = m.get("supervisors") or []
            parts = raw if isinstance(raw, list) else re.split(r",|;|/|&|\band\b", re.sub(r"\([^)]*\)", " ", raw), flags=re.I)
            names = [TITLES.sub("", " ".join(str(x).split())) for x in parts]
            out[m["name"]] = [x for x in names if x and not all(t in SUFFIXES for t in norm(x))]
    return out


def supervisor_matches(authors, supervisors, table):
    """{supervisor: 'match' or 'initial'} for the supervisors (names in `table`) found in `authors`."""
    out = {}
    for s in supervisors:
        kinds = {classify(a, s, table) for a in authors} if s in table else set()
        if kinds & {"match", "initial"}:
            out[s] = "match" if "match" in kinds else "initial"
    return out


def supervisors_on_list(authors, supervisors, table):
    """The supervisors (names in `table`) who appear anywhere in `authors`."""
    return list(supervisor_matches(authors, supervisors, table))


def classify(author, member, table):
    """'match' | 'initial' | None (other surname) | 'reject:<given>' (same surname, other person)."""
    sur, given_ok = table[member]
    a, s = norm(author), norm(sur)
    if len(a) <= len(s) or a[-len(s):] != s:
        return None
    g = a[:-len(s)]
    mid = MIDDLE.get(member)
    if mid and len(g) > 1 and g[1][0] != mid and g[0] in given_ok + [given_ok[0][0]]:
        return "reject:" + " ".join(g)  # e.g. "Ting Hon Stanford Li" is not Ting S. Li
    if g[0] in given_ok or "".join(g) in given_ok or "".join(g[:2]) in given_ok:
        return "match"
    if len(g[0]) == 1 and any(t in given_ok for t in g[1:]):
        return "match"  # "M. Jane Doe" style: initial first, then the given name
    fi = FIRST_INITIAL.get(member)
    if fi and g[0] == fi and len(g) > 1 and (g[1] in given_ok or g[1] == given_ok[0][0]):
        return "match"
    if member == "Jose Maria Palencia" and g[0] == "j" and len(g) > 1 and g[1] in ("m", "maria"):
        return "match"
    if len(g[0]) == 1 and (g[0] in {v[0] for v in given_ok} or g[0] == fi):
        return "initial"
    return "reject:" + " ".join(g)


_consecutive_failures = 0


def get(url, tries=4, log=print):
    global _consecutive_failures
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                body = r.read().decode("utf-8", "replace")
            _consecutive_failures = 0
            return body
        except Exception as e:  # 429 and timeouts are common on arXiv
            wait = 40 * (k + 1)
            log(f"   ! {type(e).__name__}: {e} -> wait {wait}s")
            time.sleep(wait)
    _consecutive_failures += 1
    if _consecutive_failures >= 3:
        raise ArxivUnavailable(f"{_consecutive_failures} consecutive requests failed; last {url[:100]}")
    raise RuntimeError(f"giving up on {url[:120]}")


def parse_api(x):
    out = []
    for e in x.split("<entry>")[1:]:
        aid = re.sub(r"v\d+$", "", re.search(r"<id>http://arxiv.org/abs/([^<]+)</id>", e).group(1))
        g = lambda p: (re.search(p, e, re.S) or [None, None])[1]
        out.append({"arxiv": aid, "v1": re.search(r"<published>([^<]+)", e).group(1)[:10],
                    "title": " ".join(html.unescape(g(r"<title>(.*?)</title>") or "").split()),
                    "abstract": " ".join(html.unescape(g(r"<summary>(.*?)</summary>") or "").split()),
                    "authors": [html.unescape(a) for a in re.findall(r"<name>([^<]+)</name>", e)],
                    "category": g(r'arxiv:primary_category[^>]*term="([^"]+)"'),
                    "journal_ref": g(r"<arxiv:journal_ref[^>]*>([^<]+)"), "doi": g(r"<arxiv:doi[^>]*>([^<]+)")})
    return out


def api_query(q, log=print):
    """All entries for an API query, checked against opensearch:totalResults."""
    out, start, total, empty_retries = [], 0, None, 0
    while True:
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
            {"search_query": q, "start": start, "max_results": 500, "sortBy": "submittedDate", "sortOrder": "descending"})
        x = get(url, log=log)
        time.sleep(4)
        m = re.search(r"<opensearch:totalResults[^>]*>(\d+)<", x)
        if m:
            total = int(m.group(1))
        ents = parse_api(x)
        if not ents:
            if total is None or start >= total:
                break
            empty_retries += 1  # the API sometimes returns an empty page mid-way
            if empty_retries > 2:
                raise RuntimeError(f"API returned {start}/{total} entries for {q[:80]}")
            time.sleep(15)
            continue
        out += ents
        start += len(ents)
        if total is not None and start >= total:
            break
        if start >= MAX_ENTRIES:
            raise RuntimeError(f"more than {MAX_ENTRIES} entries for {q[:80]}; narrow the query")
    return out


def api_by_ids(ids, log=print):
    """Full API records, with complete author lists, for a few arXiv ids."""
    out = []
    for k in range(0, len(ids), 50):
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": ",".join(ids[k:k + 50]), "max_results": 60})
        out += parse_api(get(url, log=log))
        time.sleep(4)
    return out


def web_query(term, start_date, end_date, log=print):
    """arxiv.org advanced search. Its end date is exclusive, so one day is added."""
    end_excl = (dt.date.fromisoformat(end_date) + dt.timedelta(days=1)).isoformat()
    seen, page = {}, 0
    while True:
        params = {"advanced": "", "terms-0-operator": "AND", "terms-0-term": term, "terms-0-field": "author",
                  "classification-include_cross_list": "include", "date-filter_by": "date_range",
                  "date-from_date": start_date, "date-to_date": end_excl, "date-date_type": "submitted_date_first",
                  "abstracts": "hide", "size": 200, "order": "-announced_date_first", "start": page * 200}
        x = get("https://arxiv.org/search/advanced?" + urllib.parse.urlencode(params), log=log)
        items = x.split('<li class="arxiv-result">')[1:]
        if not items and page == 0 and "Sorry, your query" not in x:
            raise RuntimeError(f"web search page for '{term}' has neither results nor the no-results notice")
        for it in items:
            m = re.search(r'href="https://arxiv.org/abs/([0-9.]+)', it)
            if not m:
                continue
            block = re.search(r'<p class="authors">(.*?)</p>', it, re.S)
            authors = [html.unescape(a).strip() for a in re.findall(r"<a [^>]*>([^<]+)</a>", block.group(1))] if block else []
            title = " ".join(html.unescape(re.sub(r"<[^>]+>", "", (re.search(r'<p class="title[^"]*">(.*?)</p>', it, re.S) or [None, ""])[1])).split())
            seen[m.group(1)] = {"arxiv": m.group(1), "title": title, "authors": authors}
        time.sleep(4)
        if len(items) < 200:
            break
        page += 1
    return list(seen.values())


def web_terms(member, table):
    sur, given_ok = table[member]
    terms = {f"{g.capitalize()} {sur}" for g in given_ok if len(g) >= 2}
    if "-" in sur:
        terms.add(sur)  # catches "J. Antwi-Danso", which the full-name query misses
    extra = {"J. Richard Bond": {"J. Richard Bond", "J. R. Bond"}, "Jose Maria Palencia": {"Jose M. Palencia", "J. M. Palencia"},
             "Ting Li": {"Ting S. Li"}, "Ue-Li Pen": {"Ue-Li Pen"}}
    return sorted(terms | extra.get(member, set()))


def api_author_clause(sur):
    return f'au:"{sur}"' if "-" in sur else f"au:{sur}"


def sweep(members, start, end, log=print, students=None):
    """members: list of team.json names. start/end: 'YYYY-MM-DD' (both inclusive).
    students: {student: [supervisors]}. A student is checked only as first author, and a hit
    is kept only when a supervisor is on the author list (Zhang and Guo would otherwise bring
    in other people's papers every week); the rest go to rec["skipped_no_supervisor"]."""
    students = students or {}
    table = member_table(list(members) + [x for sups in students.values() for x in sups])
    win = f"submittedDate:[{start.replace('-', '')}0000 TO {end.replace('-', '')}2359]"
    res = {"window": [start, end], "members": {}, "survey": {}, "errors": []}
    api_cache = {}  # members who share a surname send the same API query
    for member in members:
        sur = table[member][0]
        sups = students.get(member)
        rec = {"hits": {}, "rejected_forms": {}, "skipped_no_supervisor": {}, "api_n": None, "web_n": None}
        routes = []
        try:
            q = f"{api_author_clause(sur)} AND {win}" + (f" AND {ASTRO}" if sur in COMMON else "")
            if q not in api_cache:
                api_cache[q] = api_query(q, log=log)
            api = api_cache[q]
            rec["api_n"] = len(api)
            routes.append(("api", api))
        except ArxivUnavailable:
            raise
        except Exception as e:
            res["errors"].append({"member": member, "route": "api", "error": str(e)[:300]})
        try:
            web = []
            for term in web_terms(member, table):
                web += web_query(term, start, end, log=log)
            rec["web_n"] = len(web)
            routes.append(("web", web))
        except ArxivUnavailable:
            raise
        except Exception as e:
            res["errors"].append({"member": member, "route": "web", "error": str(e)[:300]})
        for route, ents in routes:
            for en in ents:
                for pos in ((0,) if sups is not None else (0, 1)):
                    if pos >= len(en["authors"]):
                        continue
                    c = classify(en["authors"][pos], member, table)
                    if c is None:
                        continue
                    if c.startswith("reject"):
                        rec["rejected_forms"][en["authors"][pos]] = rec["rejected_forms"].get(en["authors"][pos], 0) + 1
                        continue
                    h = rec["hits"].setdefault(en["arxiv"], {"arxiv": en["arxiv"], "title": en["title"], "position": pos + 1,
                                                              "name_as_listed": en["authors"][pos], "match": c, "routes": []})
                    if route not in h["routes"]:
                        h["routes"].append(route)
                    for k in ("v1", "category", "journal_ref", "doi"):
                        if en.get(k):
                            h[k] = en[k]
                    if sups is not None:  # either route's author list can show the supervisor
                        found = h.setdefault("supervisor_match", {})
                        for x, kind in supervisor_matches(en["authors"], sups, table).items():
                            if found.get(x) != "match":
                                found[x] = kind
        if sups is not None:
            # the arXiv search page can cut long author lists, so re-read web-only hits from the API
            recheck = [a for a, h in rec["hits"].items() if not h["supervisor_match"] and "api" not in h["routes"]]
            if recheck:
                try:
                    for en in api_by_ids(recheck, log=log):
                        if en["arxiv"] in rec["hits"]:
                            rec["hits"][en["arxiv"]]["supervisor_match"] = supervisor_matches(en["authors"], sups, table)
                except ArxivUnavailable:
                    raise
                except Exception as e:
                    res["errors"].append({"member": member, "route": "api-ids", "error": str(e)[:300]})
            for aid in [a for a, h in rec["hits"].items() if not h["supervisor_match"]]:
                rec["skipped_no_supervisor"][aid] = rec["hits"].pop(aid)
            for h in rec["hits"].values():
                h["supervisors_found"] = list(h["supervisor_match"])
        res["members"][member] = rec
        log(f"{member:26s} api={rec['api_n']} web={rec['web_n']} hits={len(rec['hits'])} rejected_forms={len(rec['rejected_forms'])}"
            + (f" skipped_no_supervisor={len(rec['skipped_no_supervisor'])}" if sups is not None else ""))
    for q in (f"abs:VENUS AND {win}", f"ti:VENUS AND {win}", f"abs:MINERVA AND {win}", f"ti:MINERVA AND {win}"):
        try:
            for en in api_query(q, log=log):
                text = en["title"] + " " + en["abstract"]
                if SURVEY_WORD.search(text) and JWST_WORD.search(text):
                    res["survey"].setdefault(en["arxiv"], {k: en[k] for k in ("arxiv", "v1", "title", "authors", "category", "journal_ref", "doi")})
        except ArxivUnavailable:
            raise
        except Exception as e:
            res["errors"].append({"query": q, "error": str(e)[:300]})
    log(f"survey-word papers: {len(res['survey'])}; errors: {len(res['errors'])}")
    return res


if __name__ == "__main__":
    team = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://raw.githubusercontent.com/Toronto-Aurora/toronto-aurora.github.io/main/site/src/data/team.json", headers=UA), timeout=60))
    names = [m["name"] for t in team["tiers"] for m in t.get("members", [])]
    out = sweep(names, sys.argv[1], sys.argv[2], students=student_supervisors(team))
    if len(sys.argv) > 3:
        json.dump(out, open(sys.argv[3], "w"), indent=1, ensure_ascii=False)
