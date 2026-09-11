# { "Depends": "py-genlayer:15qfivjvy80800rh998pcxmd2m8va1wq2qzqhz850n8ggcr4i9q0" }

from genlayer import *
import hashlib
import json
import re

# DualSource — dual-URL fact resolution under GenLayer consensus.
# Copyright (c) 2026 Valentyn Zubok. MIT License.
#
# Lifecycle:
#   open_question → attach_source (x2, freeze SHA-256) → settle
#   settle:
#     - identical content_hash → favor "tie" (deterministic, no LLM)
#     - different hashes → LLM {"prefer_a": bool} under prompt_comparative
#
# Studio-safe: JSON string state; owner as ctor arg.
# IC-only packaging: no wallet dApp in this repository.

MAX_ID_LEN = 64
MAX_Q_LEN = 800
MAX_SOURCES = 2
PREVIEW_CHARS = 280
HASH_ALGO = "sha256"
MAX_EVENTS = 200

STATUS_OPEN = "open"
STATUS_READY = "ready"
STATUS_RESOLVED = "resolved"

ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
HTTPS_URL_RE = re.compile(r"^https://[^\s<>\"']+$", re.IGNORECASE)


def _normalize_id(qid: str) -> str:
    x = str(qid).strip()
    if not x:
        raise Exception("question_id is required")
    if len(x) > MAX_ID_LEN:
        raise Exception("question_id exceeds 64 chars")
    for ch in x:
        ok = ("a" <= ch.lower() <= "z") or ("0" <= ch <= "9") or ch in "-_/"
        if not ok:
            raise Exception("question_id: only a-z, 0-9, -, _, /")
    return x


def _require_address(label: str, value: str) -> str:
    addr = str(value).strip()
    if not ADDR_RE.match(addr):
        raise Exception(f"{label} must be a 0x address")
    return addr


def _sanitize_text(label: str, text: str, max_len: int) -> str:
    cleaned = " ".join(str(text).split())
    if not cleaned:
        raise Exception(f"{label} is required")
    if len(cleaned) > max_len:
        raise Exception(f"{label} exceeds {max_len} chars")
    return cleaned


def _require_https(url: str) -> str:
    u = str(url).strip()
    if not HTTPS_URL_RE.match(u):
        raise Exception("url must be https:// with no whitespace")
    if len(u) > 2048:
        raise Exception("url exceeds 2048 chars")
    return u


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize(text: str) -> str:
    return " ".join(str(text).split())


def _capture_page(url: str) -> str:
    entry = {
        "url": url,
        "content_hash": "",
        "hash_algo": HASH_ALGO,
        "preview": "",
        "byte_len": 0,
        "status": "error",
    }
    try:
        raw = gl.get_webpage(url, mode="text")
        if raw is None or str(raw).strip() == "":
            raw = gl.get_webpage(url, mode="html")
        normalized = _normalize(raw if raw is not None else "")
        if normalized == "":
            entry["status"] = "empty"
        else:
            entry["content_hash"] = _hash_text(normalized)
            entry["preview"] = normalized[:PREVIEW_CHARS]
            entry["byte_len"] = len(normalized)
            entry["status"] = "ok"
    except Exception as exc:
        entry["preview"] = str(exc)[:120]
        entry["status"] = "error"
    return json.dumps(entry, sort_keys=True, separators=(",", ":"))


def _judge_prefer_a(question: str, preview_a: str, preview_b: str) -> str:
    """Boolean-only verdict — more stable under GenLayer comparative consensus."""
    judge = (
        "You are a GenLayer dual-source adjudicator.\n"
        "Given a QUESTION and two FROZEN source previews (A and B), decide whether "
        "SOURCE_A answers the question better than SOURCE_B.\n"
        'Return ONLY JSON: {"prefer_a": true} or {"prefer_a": false}\n'
        f"QUESTION:\n{question}\n\n"
        f"SOURCE_A:\n{preview_a}\n\n"
        f"SOURCE_B:\n{preview_b}\n"
    )
    try:
        out = gl.nondet.exec_prompt(judge, response_format="json")
    except Exception:
        out = gl.exec_prompt(judge)
    prefer_a = False
    if isinstance(out, dict):
        prefer_a = bool(out.get("prefer_a", False))
    else:
        try:
            prefer_a = bool(json.loads(str(out)).get("prefer_a", False))
        except Exception:
            prefer_a = False
    return json.dumps({"prefer_a": prefer_a}, sort_keys=True, separators=(",", ":"))


class DualSource(gl.Contract):
    owner: str
    questions_json: str
    order_json: str
    events_json: str

    def __init__(self, owner: str):
        self.owner = _require_address("owner", owner)
        self.questions_json = "{}"
        self.order_json = "[]"
        self.events_json = "[]"

    def _load_questions(self) -> dict:
        return json.loads(self.questions_json) if self.questions_json else {}

    def _save_questions(self, questions: dict) -> None:
        self.questions_json = json.dumps(questions, separators=(",", ":"))

    def _load_order(self) -> list:
        return json.loads(self.order_json) if self.order_json else []

    def _save_order(self, order: list) -> None:
        self.order_json = json.dumps(order, separators=(",", ":"))

    def _load_events(self) -> list:
        return json.loads(self.events_json) if self.events_json else []

    def _save_events(self, events: list) -> None:
        self.events_json = json.dumps(events, separators=(",", ":"))

    def _append_event(self, name: str, payload: dict) -> None:
        events = self._load_events()
        row = {"event": name}
        for k in payload:
            row[k] = payload[k]
        events.append(row)
        if len(events) > MAX_EVENTS:
            events = events[-MAX_EVENTS:]
        self._save_events(events)

    @gl.public.write
    def open_question(self, question_id: str, question: str) -> None:
        qid = _normalize_id(question_id)
        qtxt = _sanitize_text("question", question, MAX_Q_LEN)
        questions = self._load_questions()
        if qid in questions:
            raise Exception("question_id already exists")
        asker = str(gl.message.sender_address)
        questions[qid] = {
            "question_id": qid,
            "asker": asker,
            "question": qtxt,
            "status": STATUS_OPEN,
            "sources_json": "[]",
            "favor": "",
        }
        self._save_questions(questions)
        order = self._load_order()
        order.append(qid)
        self._save_order(order)
        self._append_event("QuestionOpened", {"id": qid, "asker": asker})

    @gl.public.write
    def attach_source(self, question_id: str, url: str) -> None:
        qid = _normalize_id(question_id)
        questions = self._load_questions()
        if qid not in questions:
            raise Exception("unknown question_id")
        entry = questions[qid]
        status = entry.get("status", "")
        if status != STATUS_OPEN and status != STATUS_READY:
            raise Exception("question not open for sources")

        caller = str(gl.message.sender_address)
        asker = str(entry.get("asker", ""))
        if caller != asker and caller != self.owner:
            raise Exception("only asker or owner may attach")

        sources = json.loads(entry.get("sources_json") or "[]")
        if len(sources) >= MAX_SOURCES:
            raise Exception("already have 2 sources")

        href = _require_https(url)

        def fetch_fn() -> str:
            return _capture_page(href)

        snap_json = gl.eq_principle_strict_eq(fetch_fn)
        snap = json.loads(snap_json)
        if snap.get("status") != "ok":
            raise Exception("source url fetch failed or empty")

        label = "a" if len(sources) == 0 else "b"
        sources.append(
            {
                "label": label,
                "url": href,
                "content_hash": snap.get("content_hash", ""),
                "preview": snap.get("preview", ""),
            }
        )
        entry["sources_json"] = json.dumps(sources, separators=(",", ":"))
        if len(sources) >= MAX_SOURCES:
            entry["status"] = STATUS_READY
        else:
            entry["status"] = STATUS_OPEN
        questions[qid] = entry
        self._save_questions(questions)
        self._append_event(
            "SourceAttached",
            {"id": qid, "label": label, "hash": snap.get("content_hash", "")},
        )

    @gl.public.write
    def settle(self, question_id: str) -> None:
        """Resolve from frozen sources. Same hash → tie (no LLM). Else LLM prefer_a."""
        qid = _normalize_id(question_id)
        questions = self._load_questions()
        if qid not in questions:
            raise Exception("unknown question_id")
        entry = questions[qid]
        if entry.get("status") != STATUS_READY:
            raise Exception("need exactly 2 frozen sources before settle")

        sources = json.loads(entry.get("sources_json") or "[]")
        if len(sources) != 2:
            raise Exception("need 2 sources")

        hash_a = str(sources[0].get("content_hash", ""))
        hash_b = str(sources[1].get("content_hash", ""))
        preview_a = str(sources[0].get("preview", ""))
        preview_b = str(sources[1].get("preview", ""))
        question = str(entry.get("question", ""))

        # Identical frozen evidence → deterministic tie (Studio-safe, no appeals).
        if hash_a != "" and hash_a == hash_b:

            def tie_fn() -> str:
                return json.dumps({"favor": "tie"}, sort_keys=True, separators=(",", ":"))

            favor_json = gl.eq_principle_strict_eq(tie_fn)
            favor = "tie"
            if isinstance(favor_json, str):
                try:
                    favor = str(json.loads(favor_json).get("favor", "tie"))
                except Exception:
                    favor = "tie"
        else:

            def leader_fn() -> str:
                return _judge_prefer_a(question, preview_a, preview_b)

            try:
                verdict_json = gl.eq_principle.prompt_comparative(
                    leader_fn,
                    principle="boolean field prefer_a must be identical across validators",
                )
            except Exception:
                verdict_json = gl.eq_principle_strict_eq(leader_fn)

            verdict = (
                json.loads(verdict_json) if isinstance(verdict_json, str) else verdict_json
            )
            if not isinstance(verdict, dict):
                verdict = {"prefer_a": False}
            favor = "a" if bool(verdict.get("prefer_a", False)) else "b"

        if favor not in ("a", "b", "tie"):
            favor = "tie"

        entry["favor"] = favor
        entry["status"] = STATUS_RESOLVED
        questions[qid] = entry
        self._save_questions(questions)
        self._append_event("QuestionSettled", {"id": qid, "favor": favor})

    @gl.public.view
    def get_question(self, question_id: str) -> str:
        qid = _normalize_id(question_id)
        questions = self._load_questions()
        if qid not in questions:
            return json.dumps({"error": "unknown question_id"})
        entry = dict(questions[qid])
        entry["sources"] = json.loads(entry.get("sources_json") or "[]")
        return json.dumps(entry)

    @gl.public.view
    def list_ids(self) -> str:
        return json.dumps(self._load_order())

    @gl.public.view
    def get_owner(self) -> str:
        return self.owner

    @gl.public.view
    def get_stats(self) -> str:
        questions = self._load_questions()
        counts = {}
        for q in questions.values():
            st = str(q.get("status", "?"))
            counts[st] = int(counts.get(st, 0)) + 1
        return json.dumps({"total": len(questions), "by_status": counts})
