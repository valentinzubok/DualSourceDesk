# { "Depends": "py-genlayer:15qfivjvy80800rh998pcxmd2m8va1wq2qzqhz850n8ggcr4i9q0" }

from genlayer import *
import hashlib
import json
import re

# DualSource — dual-URL fact resolution under GenLayer consensus.
# Copyright (c) 2026 Valentyn Zubok. MIT License.
#
# Lifecycle:
#   open_question → attach_source (x2, freeze SHA-256) → resolve
#   resolve: LLM picks {"favor":"a"|"b"|"tie"} from FROZEN previews only
#
# IC-only packaging: no wallet dApp in this repository.

MAX_ID_LEN = 64
MAX_Q_LEN = 800
MAX_SOURCES = 2
PREVIEW_CHARS = 280
HASH_ALGO = "sha256"

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


def _judge_favor(question: str, preview_a: str, preview_b: str) -> str:
    judge = (
        "You are a GenLayer dual-source adjudicator.\n"
        "Given a QUESTION and two FROZEN source previews (A and B), decide which "
        "source better answers the question.\n"
        'Return ONLY JSON: {"favor":"a"} or {"favor":"b"} or {"favor":"tie"}\n'
        f"QUESTION:\n{question}\n\n"
        f"SOURCE_A:\n{preview_a}\n\n"
        f"SOURCE_B:\n{preview_b}\n"
    )
    try:
        out = gl.nondet.exec_prompt(judge, response_format="json")
    except Exception:
        out = gl.exec_prompt(judge)
    favor = "tie"
    if isinstance(out, dict):
        favor = str(out.get("favor", "tie")).lower().strip()
    else:
        try:
            favor = str(json.loads(str(out)).get("favor", "tie")).lower().strip()
        except Exception:
            favor = "tie"
    if favor not in ("a", "b", "tie"):
        favor = "tie"
    return json.dumps({"favor": favor}, sort_keys=True, separators=(",", ":"))


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

    def _load(self, field: str):
        raw = getattr(self, field)
        if field in ("order_json", "events_json"):
            return json.loads(raw) if raw else []
        return json.loads(raw) if raw else {}

    def _save(self, field: str, data) -> None:
        setattr(self, field, json.dumps(data, separators=(",", ":")))

    def _append_event(self, name: str, payload: dict) -> None:
        events = self._load("events_json")
        events.append({"event": name, **payload})
        if len(events) > 200:
            events = events[-200:]
        self._save("events_json", events)

    @gl.public.write
    def open_question(self, question_id: str, question: str) -> None:
        qid = _normalize_id(question_id)
        qtxt = _sanitize_text("question", question, MAX_Q_LEN)
        questions = self._load("questions_json")
        if qid in questions:
            raise Exception("question_id already exists")
        questions[qid] = {
            "question_id": qid,
            "asker": str(gl.message.sender_address),
            "question": qtxt,
            "status": STATUS_OPEN,
            "sources": [],
            "favor": "",
        }
        self._save("questions_json", questions)
        order = self._load("order_json")
        order.append(qid)
        self._save("order_json", order)
        self._append_event("QuestionOpened", {"id": qid, "asker": questions[qid]["asker"]})

    @gl.public.write
    def attach_source(self, question_id: str, url: str) -> None:
        qid = _normalize_id(question_id)
        questions = self._load("questions_json")
        if qid not in questions:
            raise Exception("unknown question_id")
        entry = questions[qid]
        if entry.get("status") not in (STATUS_OPEN, STATUS_READY):
            raise Exception("question not open for sources")
        if str(gl.message.sender_address) != entry["asker"] and str(
            gl.message.sender_address
        ) != self.owner:
            raise Exception("only asker or owner may attach")
        sources = entry.get("sources") or []
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
        entry["sources"] = sources
        entry["status"] = STATUS_READY if len(sources) >= MAX_SOURCES else STATUS_OPEN
        questions[qid] = entry
        self._save("questions_json", questions)
        self._append_event(
            "SourceAttached",
            {"id": qid, "label": label, "hash": snap.get("content_hash", "")},
        )

    @gl.public.write
    def resolve(self, question_id: str) -> None:
        """LLM picks favor a|b|tie from frozen source previews. Consensus on favor only."""
        qid = _normalize_id(question_id)
        questions = self._load("questions_json")
        if qid not in questions:
            raise Exception("unknown question_id")
        entry = questions[qid]
        if entry.get("status") != STATUS_READY:
            raise Exception("need exactly 2 frozen sources before resolve")
        sources = entry.get("sources") or []
        if len(sources) != 2:
            raise Exception("need 2 sources")

        preview_a = sources[0].get("preview", "")
        preview_b = sources[1].get("preview", "")
        question = entry.get("question", "")

        def leader_fn() -> str:
            return _judge_favor(question, preview_a, preview_b)

        try:
            verdict_json = gl.eq_principle.prompt_comparative(
                leader_fn,
                principle="string field favor must be identical across validators (a|b|tie)",
            )
        except Exception:
            verdict_json = gl.eq_principle_strict_eq(leader_fn)

        verdict = json.loads(verdict_json) if isinstance(verdict_json, str) else verdict_json
        if not isinstance(verdict, dict):
            verdict = {"favor": "tie"}
        favor = str(verdict.get("favor", "tie")).lower().strip()
        if favor not in ("a", "b", "tie"):
            favor = "tie"

        entry["favor"] = favor
        entry["status"] = STATUS_RESOLVED
        questions[qid] = entry
        self._save("questions_json", questions)
        self._append_event("QuestionResolved", {"id": qid, "favor": favor})

    @gl.public.view
    def get_question(self, question_id: str) -> str:
        qid = _normalize_id(question_id)
        questions = self._load("questions_json")
        if qid not in questions:
            return json.dumps({"error": "unknown question_id"})
        return json.dumps(questions[qid])

    @gl.public.view
    def list_ids(self) -> str:
        return json.dumps(self._load("order_json"))

    @gl.public.view
    def get_owner(self) -> str:
        return self.owner

    @gl.public.view
    def get_stats(self) -> str:
        questions = self._load("questions_json")
        counts = {}
        for q in questions.values():
            st = q.get("status", "?")
            counts[st] = counts.get(st, 0) + 1
        return json.dumps({"total": len(questions), "by_status": counts})
