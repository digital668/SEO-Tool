"""Makes drafts read like a person wrote them, without "spinning".

Three free layers:
1. Editor pass: Claude re-edits the draft as a human editor would (varied
   sentence rhythm, contractions, direct address, concrete examples, cut
   filler) while keeping every heading, link and fact.
2. AI-phrase scrubber: removes or replaces the stock phrases that make
   text sound machine-written ("delve", "in today's fast-paced world", …).
3. Readability metrics (offline, no API): Flesch reading ease, sentence-
   length variation, passive voice, long paragraphs, leftover AI phrases.

Deliberately NOT used: synonym-swapping "humanizer"/spinner tools. They
damage meaning and grammar, and spun text is itself a Google spam signal.
"""
from __future__ import annotations

import re
import statistics

from bs4 import BeautifulSoup, NavigableString

from . import llm
from .config import Site
from .textutil import html_to_text

# phrase (regex, case-insensitive) → replacement ("" = delete)
AI_PHRASES: list[tuple[str, str]] = [
    (r"\bin today'?s (fast-paced|digital|modern|ever-changing) (world|age|landscape),?\s*", ""),
    (r"\bin the ever-evolving (world|landscape) of\b", "in"),
    (r"\bit'?s (important|worth|crucial) to (note|remember|mention) that\s*", ""),
    (r"\bit is (important|worth|crucial) to (note|remember|mention) that\s*", ""),
    (r"\bin conclusion,?\s*", ""),
    (r"\bto sum (it )?up,?\s*", ""),
    (r"\bwhen it comes to\b", "with"),
    (r"\bdelve(s|d)? into\b", "look\\1 at"),
    (r"\bdelving into\b", "looking at"),
    (r"\bdive deep into\b", "look closely at"),
    (r"\bunlock(s|ing)? the (full )?(power|potential) of\b", "make the most of"),
    (r"\bnavigat(e|ing) the (complexities|intricacies|world) of\b", "deal with"),
    (r"\ba testament to\b", "proof of"),
    (r"\b(rich |vibrant )?tapestry of\b", "mix of"),
    (r"\bembark(s|ed)? on\b", "start\\1"),
    (r"\bembarking on\b", "starting"),
    (r"\bgame[- ]changer\b", "big improvement"),
    (r"\bseamless(ly)?\b", "smooth\\1"),
    (r"\bleverag(e|es|ed|ing)\b", "us\\1"),
    (r"\butiliz(e|es|ed|ing)\b", "us\\1"),
    (r"\belevate(s|d)? your\b", "improve\\1 your"),
    (r"\bin the realm of\b", "in"),
    (r"\brealm\b", "area"),
    (r"\bmyriad of\b", "lots of"),
    (r"\bplethora of\b", "plenty of"),
    (r"\bmoreover,\s*", "Also, "),
    (r"\bfurthermore,\s*", "Plus, "),
    (r"\badditionally,\s*", "Also, "),
    (r"\bin essence,?\s*", ""),
    (r"\bultimately,\s*", ""),
    (r"\blook no further\b", "you're in the right place"),
    (r"\bwhether you'?re a seasoned [a-z]+ or (a )?(newcomer|beginner|novice),?\s*", ""),
    (r"\bstands as a\b", "is a"),
    (r"\bserves as a\b", "is a"),
    (r"\bboasts\b", "has"),
    (r"\bcutting-edge\b", "modern"),
    (r"\bever-evolving\b", "changing"),
    (r"\bharness(es|ing)? the power of\b", "use"),
    (r"\bpivotal\b", "key"),
    (r"\bparamount\b", "essential"),
    (r"\brobust\b", "strong"),
    (r"\bcrucial\b", "key"),
    (r"\bholistic\b", "all-round"),
    (r"\bcomprehensive guide\b", "guide"),
    (r"\bmeticulous(ly)?\b", "careful\\1"),
    (r"\bbustling\b", "busy"),
    (r"\bsynergy\b", "teamwork"),
]
_COMPILED = [(re.compile(p, re.I), r) for p, r in AI_PHRASES]
DETECT = [rx for rx, _ in _COMPILED]


def _fix_case(original: str, new: str) -> str:
    if new and original[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def scrub(html: str) -> tuple[str, int]:
    """Replace AI phrases inside text nodes only (tags/links untouched). Returns (html, replacements)."""
    soup = BeautifulSoup(html, "lxml")
    count = 0
    for node in list(soup.find_all(string=True)):
        if not isinstance(node, NavigableString) or node.parent.name in ("script", "style", "code"):
            continue
        text = str(node)
        new = text
        for rx, rep in _COMPILED:
            def sub(m, rep=rep):
                return _fix_case(m.group(0), m.expand(rep))
            new, n = rx.subn(sub, new)
            count += n
        if new != text:
            # re-capitalise a sentence start left lowercase by a deletion
            new = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), new)
            node.replace_with(new)
    body = soup.body
    out = "".join(str(c) for c in body.contents) if body else str(soup)
    return out, count


# ── offline readability metrics ───────────────────────────
def _syllables(word: str) -> int:
    w = word.lower().strip(".,!?;:'\"()")
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text) if len(s.split()) >= 3]


def metrics(html: str) -> dict:
    text = html_to_text(html)
    sents = _sentences(text)
    wl = [len(s.split()) for s in sents] or [0]
    wds = text.split()
    syl = sum(_syllables(w) for w in wds)
    flesch = 206.835 - 1.015 * (len(wds) / max(len(sents), 1)) - 84.6 * (syl / max(len(wds), 1))
    passive = len(re.findall(r"\b(is|are|was|were|be|been|being)\s+(\w+ed|\w+en)\b", text, re.I))
    soup = BeautifulSoup(html, "lxml")
    long_paras = sum(1 for p in soup.find_all("p") if len(p.get_text().split()) > 120)
    ai_left = sorted({m.group(0).lower() for rx in DETECT for m in rx.finditer(text)})
    return {
        "flesch": round(flesch, 1),
        "avg_sentence_words": round(statistics.mean(wl), 1),
        "sentence_variation": round(statistics.pstdev(wl), 1),   # higher = more human rhythm
        "passive_pct": round(100 * passive / max(len(sents), 1), 1),
        "long_paragraphs": long_paras,
        "ai_phrases_left": ai_left,
        "contractions": len(re.findall(r"\b\w+'(s|re|ve|ll|d|t|m)\b", text)),
    }


def passes(m: dict) -> bool:
    return (m["flesch"] >= 45 and m["sentence_variation"] >= 5 and not m["ai_phrases_left"]
            and m["passive_pct"] <= 15)


EDIT_SCHEMA = {"type": "object", "properties": {"content_html": {"type": "string"}},
               "required": ["content_html"]}


def humanize(site: Site, article: dict) -> tuple[dict, dict]:
    before = metrics(article["content_html"])
    prompt = f"""You are a senior human editor at {site.name}. Edit this draft so it reads like an
experienced person in this field wrote it for {site.audience}. Tone: {site.tone}.

Editing rules:
- Keep EVERY heading (same order and wording unless a heading is awkward), every <a href> link,
  every table and list, and every fact. Do not add new facts, statistics or claims.
- Keep the focus keyword "{article['focus_keyword']}" in the first paragraph and in at least one H2/H3,
  used naturally (around 1 use per 100 words — never stuffed).
- Vary sentence length: mix short punchy sentences with longer ones. Use contractions. Speak to the
  reader as "you". Prefer active voice.
- Replace vague statements with concrete specifics or examples that are already implied by the draft.
- Remove filler and stock AI phrasing (e.g. "delve", "in today's world", "it's important to note",
  "moreover", "furthermore", "in conclusion", "unlock the potential", "seamless", "robust", "crucial").
- Paragraphs of 1–4 sentences, none over 100 words.
- Return the full edited body HTML (same allowed tags: h2, h3, p, ul, ol, li, table, thead, tbody,
  tr, th, td, a, strong, em). No <h1>, no markdown.

Current readability: {before}

DRAFT:
{article['content_html']}"""
    out, usage = llm.structured(system="You are a meticulous human copy editor.", prompt=prompt,
                                tool_name="submit_edit", schema=EDIT_SCHEMA, max_tokens=16000)
    edited = out.get("content_html") or article["content_html"]
    # never accept an edit that lost most of the article or its links
    if len(html_to_text(edited)) < 0.75 * len(html_to_text(article["content_html"])) or \
            edited.count("<a ") < article["content_html"].count("<a ") * 0.6:
        edited = article["content_html"]
    edited, replaced = scrub(edited)
    article["content_html"] = edited
    article["humanize"] = {"before": before, "after": metrics(edited), "scrubbed": replaced}
    article["humanize"]["ok"] = passes(article["humanize"]["after"])
    return article, usage
