#!/usr/bin/env python3
"""
Aether Memory System — Backend Script  v3.0
以太记忆系统 · 后端存储层

Two-tier storage: hot JSON (active context) + cold JSONL archive (never deleted).
Episodic entries are archived when fuzzy/old, not silently dropped.
Associative Memory Network: memories form webs of association — recalling one
memory passively strengthens related memories (Spreading Activation Theory).

Commands:
  load        [user_id]            Load memory → print <memory_load> XML
  save        [user_id]            Read <memory_snapshot> from stdin → persist
  apply       [user_id]            Read assistant text from stdin → apply <mem_ops>
  init        [user_id]            Create a blank memory file
  status      [user_id]            Memory statistics
  list                             All users with saved memories
  history     [user_id]            Session backup history
  consolidate [user_id]            Archive fuzzy entries, rebuild archive summary
  forget      [user_id] --id ID    Move one episodic entry to archive
  prune       [user_id]            Archive all fuzzy / low-importance entries
  recall      [user_id] kw...      Search cold archive for keywords
  export      [user_id]            Full JSON export (hot + archive)
  drift       [user_id]            Emotional trajectory analysis across sessions

Options:
  --dir DIR      Override storage directory
  --force        Allow overwrite (init)
  --json         Raw JSON output (load)
  -v, --verbose  Verbose stderr
"""

import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DIRS = [
    Path(".aether") / "memories",
    Path.home() / ".aether" / "memories",
]

EPISODIC_HOT_CAPACITY   = 40   # Hard cap on hot episodic entries
EPISODIC_ARCHIVE_THRESH = 30   # Auto-archive fuzzy entries when hot > this
BEHAVIORAL_CAPACITY     = 25
NOTES_CAPACITY          = 20
ARCHIVE_TOP_N           = 6    # Important entries shown in archive summary

# Spaced Repetition System (SRS) constants
REINFORCE_BOOST_PER_COUNT = 0.6  # Effective ★ added per reinforcement (cap: +2.4)
REINFORCE_MAX_BOOST       = 2.4
VALENCE_TRANSITION_BOOST  = 1.0  # Emotion-change marker "→" in raw
VALENCE_NEGATIVE_BOOST    = 0.5  # Negative / high-arousal emoji in raw
PRIMACY_SESSION_CUTOFF    = 2    # Sessions ≤ this are "early" and get primacy boost
PRIMACY_BOOST             = 1.0
RECENCY_PROTECTED         = 5    # Most-recent N hot entries immune to auto-archive
# Negative-valence emoji set (Baumeister negativity bias)
NEGATIVE_EMOTIONS = frozenset("😢😤💢🥺😭😰😣😖😫😔😞")

# Associative Memory Network (Collins & Loftus, 1975 — Spreading Activation)
ASSOCIATION_PASSIVE_BOOST  = 0.15  # Boost to associated entries when one is reinforced
ASSOCIATION_MAX_BOOST      = 1.2   # Cap on total association-derived boost per entry
ASSOCIATION_MAX_LINKS      = 5     # Max explicit associations per entry
TEMPORAL_PROXIMITY_WINDOW  = 1     # Sessions within this window auto-link (weak)
EMOTIONAL_RESONANCE_EMOJIS = {
    "positive": frozenset("😊😄😆🥰😍🤗💖✨🎉"),
    "negative": frozenset("😢😤💢🥺😭😰😣😖😫😔😞"),
    "neutral":  frozenset("😐🤔📝💡"),
}

BLANK_MEMORY: dict = {
    "user_id": "default",
    "session": 0,
    "last_updated": None,
    "modules": {
        "semantic_profile": "[尚未建立档案]",
        "notes": [],
        "episodic_memory": [],
        "relationship_map": (
            "熟悉度: 陌生人\n"
            "信任度: 未知\n"
            "好感度: 无感\n"
            "互动基调: 待观察\n"
            "关键转折点: 无"
        ),
        "behavioral_memory": [],
        "emotional_sediment": "新的对话。新的人。保持距离，先观察。",
    },
    "archive": {
        "summary": "",
        "entry_count": 0,
        "sessions_archived": 0,
        "relationship_arc": [],
    },
}


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _safe(user_id: str) -> str:
    return re.sub(r"[^\w\-.]", "_", user_id)


def resolve_dir(dir_arg: str | None) -> Path:
    if dir_arg:
        d = Path(dir_arg)
    else:
        d = next((p for p in DEFAULT_DIRS if p.exists()), DEFAULT_DIRS[0])
    d.mkdir(parents=True, exist_ok=True)
    return d


def memory_path(d: Path, user_id: str) -> Path:
    return d / f"{_safe(user_id)}.json"


def archive_path(d: Path, user_id: str) -> Path:
    return d / f"{_safe(user_id)}.archive.jsonl"


# ---------------------------------------------------------------------------
# Hot JSON load / save
# ---------------------------------------------------------------------------

def load_memory(d: Path, user_id: str) -> dict:
    path = memory_path(d, user_id)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                mem = json.load(f)
            # Migrate: ensure new keys exist
            mem.setdefault("archive", dict(BLANK_MEMORY["archive"]))
            mem["modules"].setdefault("notes", [])
            return mem
        except (json.JSONDecodeError, OSError) as e:
            print(f"[aether] Warning: could not read {path}: {e}", file=sys.stderr)
    mem = json.loads(json.dumps(BLANK_MEMORY))
    mem["user_id"] = user_id
    return mem


def save_memory(d: Path, user_id: str, memory: dict) -> None:
    path = memory_path(d, user_id)
    session = memory.get("session", 0)
    # Session-numbered backup (keep history)
    if path.exists() and session > 0:
        backup = d / f"{_safe(user_id)}.s{session:03d}.json"
        if not backup.exists():  # Don't overwrite existing backups
            try:
                backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            except OSError:
                pass
    memory["last_updated"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Cold archive helpers
# ---------------------------------------------------------------------------

def load_archive_entries(d: Path, user_id: str) -> list[dict]:
    path = archive_path(d, user_id)
    if not path.exists():
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def append_to_archive(d: Path, user_id: str, entries: list[dict], session: int) -> None:
    if not entries:
        return
    path = archive_path(d, user_id)
    with open(path, "a", encoding="utf-8") as f:
        for e in entries:
            record = dict(e)
            record["archived_session"] = session
            record["archived_at"] = datetime.now().isoformat()
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_archive_summary(archive_entries: list[dict], relationship_arc: list[dict]) -> str:
    if not archive_entries and not relationship_arc:
        return ""
    lines = []
    if archive_entries:
        # Flashbulb entries always shown first (never let them disappear from summary)
        flashbulb = [e for e in archive_entries if e.get("flashbulb")]
        rest      = [e for e in archive_entries if not e.get("flashbulb")]
        # Remaining slots filled by highest effective_importance
        rest_top  = sorted(rest, key=lambda e: -e.get("importance", 3))[:max(0, ARCHIVE_TOP_N - len(flashbulb))]
        top       = flashbulb + rest_top
        lines.append(f"归档记忆 {len(archive_entries)} 条。重要事件：")
        for e in top:
            sess  = e.get("archived_session", "?")
            raw   = e.get("raw", "").split("|")[-1].strip()[:40]
            imp   = "★" * e.get("importance", 3)
            fb    = " [⚡]" if e.get("flashbulb") else ""
            rc    = e.get("reinforcement_count", 0)
            srs   = f" ×{rc}" if rc > 0 else ""
            lines.append(f"  {imp}{fb}{srs} [S{sess}] {raw}")
    if relationship_arc and len(relationship_arc) >= 2:
        # Sample up to 5 arc points evenly
        arc = relationship_arc
        step = max(1, len(arc) // 5)
        sampled = arc[::step]
        if arc[-1] not in sampled:
            sampled.append(arc[-1])
        arc_str = " → ".join(f"S{a['session']}:{a['familiarity']}" for a in sampled)
        lines.append(f"关系弧线: {arc_str}")
    return "\n".join(lines)


def track_relationship(memory: dict) -> None:
    """Snapshot current familiarity into the relationship arc if it changed."""
    rm = memory.get("modules", {}).get("relationship_map", "")
    m = re.search(r"熟悉度[：:]\s*(.+?)(?:\n|$)", rm)
    if not m:
        return
    familiarity = m.group(1).strip()
    arc: list[dict] = memory.setdefault("archive", {}).setdefault("relationship_arc", [])
    session = memory.get("session", 0)
    if not arc or arc[-1].get("familiarity") != familiarity:
        arc.append({
            "session": session,
            "familiarity": familiarity,
            "date": datetime.now().isoformat()[:10],
        })


# ---------------------------------------------------------------------------
# Spaced Repetition System — effective importance
# ---------------------------------------------------------------------------

def emotional_valence_boost(raw: str) -> float:
    """
    Automatically score emotional intensity from raw text (Baumeister 2001,
    Cahill & McGaugh 1995). Two signals:
      • Emotion-change arrow "→"  →  +VALENCE_TRANSITION_BOOST (high arousal)
      • Negative-valence emoji    →  +VALENCE_NEGATIVE_BOOST   (negativity bias)
    Combined, negative turning-point memories can earn up to +1.5 over base ★.
    """
    boost = 0.0
    if "→" in raw:
        boost += VALENCE_TRANSITION_BOOST
    if any(ch in raw for ch in NEGATIVE_EMOTIONS):
        boost += VALENCE_NEGATIVE_BOOST
    return boost


def effective_importance(entry: dict, current_session: int) -> float:
    """
    Compute the true archival priority of an episodic entry.

    Components (all additive on top of the author-assigned ★ base):
    ① Spaced-repetition boost   — each <reinforce> adds REINFORCE_BOOST_PER_COUNT,
                                   capped at REINFORCE_MAX_BOOST.  (Ebbinghaus 1885)
    ② Emotional valence boost   — auto-scored from emoji; transitions and negative
                                   emotions decay slower.  (Baumeister 2001)
    ③ Primacy boost             — entries born in the first PRIMACY_SESSION_CUTOFF
                                   sessions get +PRIMACY_BOOST.  (Atkinson & Shiffrin 1968)
    ④ Association boost         — passive boost from spreading activation when
                                   linked memories are reinforced.  (Collins & Loftus 1975)

    Flashbulb entries return ∞ (99) — they are indestructible.
    """
    if entry.get("flashbulb"):
        return 99.0
    base = float(entry.get("importance", 3))
    # ① SRS boost
    rc = entry.get("reinforcement_count", 0)
    srs = min(rc * REINFORCE_BOOST_PER_COUNT, REINFORCE_MAX_BOOST)
    # ② Valence
    valence = emotional_valence_boost(entry.get("raw", ""))
    # ③ Primacy (only if first_session was recorded at creation time)
    fs = entry.get("first_session")
    primacy = PRIMACY_BOOST if (fs is not None and fs <= PRIMACY_SESSION_CUTOFF) else 0.0
    # ④ Association boost (spreading activation)
    assoc = min(entry.get("association_boost", 0.0), ASSOCIATION_MAX_BOOST)
    return base + srs + valence + primacy + assoc


# ---------------------------------------------------------------------------
# Associative Memory Network — Spreading Activation (Collins & Loftus 1975)
# ---------------------------------------------------------------------------

def _extract_emotion_class(raw: str) -> str:
    """Classify entry's dominant emotion for resonance linking."""
    for cls, emojis in EMOTIONAL_RESONANCE_EMOJIS.items():
        if any(ch in raw for ch in emojis):
            return cls
    return "neutral"


def _extract_keywords(raw: str) -> set[str]:
    """Extract meaningful keywords from raw text for topic-based linking."""
    # Strip the ID/star prefix, keep the summary part
    parts = raw.split("|", 1)
    text = parts[-1].strip() if len(parts) > 1 else raw
    # Remove markers, punctuation, split into tokens
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"[#★☆⚡\d]", "", text)
    tokens = set(re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]{3,}", text))
    return tokens


def compute_auto_associations(entries: list[dict]) -> dict[str, list[str]]:
    """
    Build weak auto-associations between entries based on:
    1. Temporal proximity (same or adjacent sessions)
    2. Emotional resonance (same emotion class)
    3. Keyword co-occurrence (shared topic terms)

    Returns {entry_id: [associated_ids]} — only new auto-links, not explicit ones.
    """
    if len(entries) < 2:
        return {}

    associations: dict[str, set[str]] = {e["id"]: set() for e in entries}

    for i, a in enumerate(entries):
        a_session = a.get("first_session") or 0
        a_emotion = _extract_emotion_class(a.get("raw", ""))
        a_keywords = _extract_keywords(a.get("raw", ""))

        for b in entries[i + 1:]:
            b_session = b.get("first_session") or 0
            score = 0.0

            # Temporal proximity
            if abs(a_session - b_session) <= TEMPORAL_PROXIMITY_WINDOW:
                score += 0.4

            # Emotional resonance
            b_emotion = _extract_emotion_class(b.get("raw", ""))
            if a_emotion == b_emotion and a_emotion != "neutral":
                score += 0.3

            # Keyword co-occurrence
            b_keywords = _extract_keywords(b.get("raw", ""))
            overlap = a_keywords & b_keywords
            if len(overlap) >= 1:
                score += 0.3 * min(len(overlap), 3)

            # Link if score above threshold
            if score >= 0.6:
                if len(associations[a["id"]]) < ASSOCIATION_MAX_LINKS:
                    associations[a["id"]].add(b["id"])
                if len(associations[b["id"]]) < ASSOCIATION_MAX_LINKS:
                    associations[b["id"]].add(a["id"])

    return {k: sorted(v) for k, v in associations.items() if v}


def spreading_activation(entries: list[dict], reinforced_id: str) -> list[tuple[str, float]]:
    """
    When a memory is reinforced, compute passive boosts for associated entries.
    Returns [(entry_id, boost_amount)] for entries that should receive a passive boost.
    """
    source = next((e for e in entries if e["id"] == reinforced_id), None)
    if not source:
        return []

    # Combine explicit + auto associations
    explicit_links = set(source.get("associations", []))
    auto_links = compute_auto_associations(entries).get(reinforced_id, [])
    all_linked = explicit_links | set(auto_links)

    boosts = []
    for linked_id in all_linked:
        target = next((e for e in entries if e["id"] == linked_id), None)
        if target and not target.get("flashbulb"):
            current_assoc_boost = target.get("association_boost", 0.0)
            if current_assoc_boost < ASSOCIATION_MAX_BOOST:
                boost = min(ASSOCIATION_PASSIVE_BOOST,
                            ASSOCIATION_MAX_BOOST - current_assoc_boost)
                boosts.append((linked_id, boost))

    return boosts


def apply_spreading_activation(entries: list[dict], reinforced_id: str) -> int:
    """
    Apply spreading activation after a reinforce operation.
    Returns count of entries that received a passive boost.
    """
    boosts = spreading_activation(entries, reinforced_id)
    count = 0
    for entry_id, boost in boosts:
        for e in entries:
            if e["id"] == entry_id:
                e["association_boost"] = e.get("association_boost", 0.0) + boost
                count += 1
                break
    return count


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_importance(text: str) -> int:
    return max(1, min(5, text.count("★")))


def parse_episodic_entry(raw: str) -> dict:
    raw = raw.strip()
    m = re.match(r"(#e\d+)\s+((?:★|☆)+)\s+(.+?)\s+(.+?)\s*\|\s*(.+)", raw)
    base = {
        # SRS fields — preserved across updates (caller must merge into existing)
        "reinforcement_count":    0,
        "last_reinforced_session": None,
        "first_session":          None,   # Set to current session at creation time
        "flashbulb":              "[⚡]" in raw,
        "suppressed":             "[已压制]" in raw,
        "fuzzy":                  "[模糊]" in raw,
        # Associative Memory Network fields
        "associations":           [],     # Explicit links to related entries
        "association_boost":      0.0,    # Passive boost from spreading activation
    }
    if m:
        return {**base, "id": m.group(1).lstrip("#"), "raw": raw,
                "importance": parse_importance(m.group(2))}
    id_m = re.match(r"#(e\d+)", raw)
    return {**base, "id": id_m.group(1) if id_m else "e??", "raw": raw, "importance": 3}


def parse_behavioral_entry(raw: str) -> dict:
    raw = raw.strip()
    source_ids = [f"e{s}" for s in re.findall(r"#e(\d+)", raw)]
    return {
        "raw": raw,
        "source_ids": source_ids,
        "fuzzy_source": "[来源已模糊]" in raw,
    }


def parse_note_entry(raw: str, next_id: int) -> dict:
    raw = raw.strip()
    return {
        "id": f"n{next_id:02d}",
        "raw": raw,
        "created_session": 0,  # Caller fills this in
    }


def parse_mem_ops(text: str) -> list[dict]:
    ops: list[dict] = []
    for block in re.findall(r"<mem_ops>(.*?)</mem_ops>", text, re.DOTALL):
        for target, content in re.findall(
            r'<write\s+target="([^"]+)">(.*?)</write>', block, re.DOTALL
        ):
            ops.append({"op": "write", "target": target.strip(), "content": content.strip()})
        for target, content in re.findall(
            r'<update\s+target="([^"]+)">(.*?)</update>', block, re.DOTALL
        ):
            ops.append({"op": "update", "target": target.strip(), "content": content.strip()})
        for target, id_, reason in re.findall(
            r'<forget\s+target="([^"]+)"\s+id="([^"]+)">(.*?)</forget>', block, re.DOTALL
        ):
            ops.append({"op": "forget", "target": target.strip(), "id": id_.strip(), "reason": reason.strip()})
        for target, id_, reason in re.findall(
            r'<suppress\s+target="([^"]+)"\s+id="([^"]+)">(.*?)</suppress>', block, re.DOTALL
        ):
            ops.append({"op": "suppress", "target": target.strip(), "id": id_.strip(), "reason": reason.strip()})
        # <note> — permanent fact
        for content in re.findall(r"<note>(.*?)</note>", block, re.DOTALL):
            ops.append({"op": "note", "content": content.strip()})
        # <merge ids="e03,e07"> — merge episodes into one
        for ids_str, content in re.findall(
            r'<merge\s+ids="([^"]+)">(.*?)</merge>', block, re.DOTALL
        ):
            ids = [i.strip().lstrip("#") for i in ids_str.split(",")]
            ops.append({"op": "merge", "ids": ids, "content": content.strip()})
        # SRS: <reinforce id="eNN"/> or <reinforce id="eNN">reinterpretation</reinforce>
        for id_, note in re.findall(
            r'<reinforce\s+id="([^"]+)">(.*?)</reinforce>', block, re.DOTALL
        ):
            ops.append({"op": "reinforce", "id": id_.strip().lstrip("#"), "note": note.strip()})
        for id_ in re.findall(r'<reinforce\s+id="([^"]+)"\s*/>', block):
            ops.append({"op": "reinforce", "id": id_.strip().lstrip("#"), "note": ""})
        # SRS: <flashbulb id="eNN"/> — mark as indestructible
        for id_ in re.findall(r'<flashbulb\s+id="([^"]+)"\s*/?>', block):
            ops.append({"op": "flashbulb", "id": id_.strip().lstrip("#")})
        # Confidence: <retract id="eNN">reason</retract> — user correction, moves to archive
        for id_, reason in re.findall(
            r'<retract\s+id="([^"]+)">(.*?)</retract>', block, re.DOTALL
        ):
            ops.append({"op": "retract", "id": id_.strip().lstrip("#"), "reason": reason.strip()})
        # Associative Memory Network: <associate ids="eNN,eMM"/> — explicit link
        for ids_str in re.findall(r'<associate\s+ids="([^"]+)"\s*/>', block):
            ids = [i.strip().lstrip("#") for i in ids_str.split(",")]
            if len(ids) >= 2:
                ops.append({"op": "associate", "ids": ids})
    return ops


def parse_snapshot(text: str) -> tuple[dict | None, int | None]:
    snap_m = re.search(
        r'<memory_snapshot(?:\s+session="(\d+)")?[^>]*>(.*?)</memory_snapshot>',
        text, re.DOTALL,
    )
    if not snap_m:
        return None, None

    session = int(snap_m.group(1)) if snap_m.group(1) else None
    body = snap_m.group(2)
    modules: dict = {}

    for mod in ["semantic_profile", "relationship_map", "episodic_memory",
                "behavioral_memory", "emotional_sediment", "notes"]:
        m = re.search(rf"<{mod}>(.*?)</{mod}>", body, re.DOTALL)
        if not m:
            continue
        content = "\n".join(ln.strip() for ln in m.group(1).splitlines()).strip()
        if mod == "episodic_memory":
            modules[mod] = [
                parse_episodic_entry(ln)
                for ln in content.splitlines()
                if ln.strip().startswith("#e")
            ]
        elif mod == "behavioral_memory":
            modules[mod] = [
                parse_behavioral_entry(ln)
                for ln in content.splitlines()
                if ln.strip()
            ]
        elif mod == "notes":
            entries = []
            for i, ln in enumerate(content.splitlines(), 1):
                ln = ln.strip()
                if ln:
                    # Snapshot lines may already have "nXX: " prefix
                    m2 = re.match(r"n\d+:\s*(.*)", ln)
                    raw = m2.group(1).strip() if m2 else ln
                    entries.append({"id": f"n{i:02d}", "raw": raw, "created_session": 0})
            modules[mod] = entries
        else:
            modules[mod] = content

    return modules, session


# ---------------------------------------------------------------------------
# Core memory operations
# ---------------------------------------------------------------------------

def _archive_entries(d: Path, user_id: str, memory: dict, entries: list[dict]) -> None:
    """Move a list of episodic entries to cold archive, update summary."""
    if not entries:
        return
    session = memory.get("session", 0)
    append_to_archive(d, user_id, entries, session)
    arch = memory.setdefault("archive", dict(BLANK_MEMORY["archive"]))
    arch["entry_count"] = arch.get("entry_count", 0) + len(entries)
    # Rebuild summary from full archive
    all_archived = load_archive_entries(d, user_id)
    arch["summary"] = build_archive_summary(all_archived, arch.get("relationship_arc", []))


def auto_consolidate(d: Path, user_id: str, memory: dict) -> int:
    """
    Archive fuzzy entries when hot tier exceeds threshold.
    SRS rules applied:
      • Flashbulb entries ([⚡]) are NEVER archived automatically
      • Most-recent RECENCY_PROTECTED entries are immune to auto-archive
      • Archival priority uses effective_importance (not raw ★)
    Returns count archived.
    """
    ep: list[dict] = memory.get("modules", {}).get("episodic_memory", [])
    if len(ep) <= EPISODIC_ARCHIVE_THRESH:
        return 0
    session = memory.get("session", 0)
    recent_ids   = {e["id"] for e in ep[-RECENCY_PROTECTED:]}
    protected_ids = recent_ids | {e["id"] for e in ep if e.get("flashbulb")}

    # Fuzzy candidates (explicitly faded) — exclude protected
    candidates = [e for e in ep if e.get("fuzzy") and e["id"] not in protected_ids]
    if not candidates and len(ep) > EPISODIC_HOT_CAPACITY:
        # Safety valve: pick lowest-effective-importance non-protected entries
        sortable   = [e for e in ep if e["id"] not in protected_ids]
        sortable.sort(key=lambda e: effective_importance(e, session))
        overflow   = len(ep) - EPISODIC_HOT_CAPACITY
        candidates = sortable[:overflow]

    if candidates:
        evict_ids = {e["id"] for e in candidates}
        memory["modules"]["episodic_memory"] = [e for e in ep if e["id"] not in evict_ids]
        _archive_entries(d, user_id, memory, candidates)
    return len(candidates)


def apply_ops(d: Path, user_id: str, memory: dict, ops: list[dict]) -> dict:
    modules = memory.setdefault("modules", {})
    session = memory.get("session", 0)

    for op in ops:
        o = op["op"]

        # ── write / update ────────────────────────────────────────────────
        if o in ("write", "update"):
            target = op["target"]
            content = op["content"]

            # Memory integrity validation (anti-injection)
            safe, reason = validate_entry_integrity(content)
            if not safe:
                print(f"[aether] {reason}", file=sys.stderr)
                continue

            if target == "episodic_memory":
                entries: list[dict] = modules.setdefault("episodic_memory", [])
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    entry = parse_episodic_entry(line)
                    existing = next((e for e in entries if e["id"] == entry["id"]), None)
                    if existing and o == "update":
                        # Preserve SRS history across updates
                        entry["reinforcement_count"]    = existing.get("reinforcement_count", 0)
                        entry["last_reinforced_session"] = existing.get("last_reinforced_session")
                        entry["first_session"]          = existing.get("first_session", session)
                        existing.update(entry)
                    else:
                        entry["first_session"] = session   # Primacy: record birth session
                        entries.append(entry)
                # Hard cap enforcement — use effective_importance, respect recency
                if len(entries) > EPISODIC_HOT_CAPACITY:
                    recent_ids = {e["id"] for e in entries[-RECENCY_PROTECTED:]}
                    sortable   = [e for e in entries if e["id"] not in recent_ids]
                    sortable.sort(key=lambda e: effective_importance(e, session))
                    evict      = sortable[:len(entries) - EPISODIC_HOT_CAPACITY]
                    evict_ids  = {e["id"] for e in evict}
                    modules["episodic_memory"] = [e for e in entries if e["id"] not in evict_ids]
                    _archive_entries(d, user_id, memory, evict)

            elif target == "behavioral_memory":
                entries = modules.setdefault("behavioral_memory", [])
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        entries.append(parse_behavioral_entry(line))
                if len(entries) > BEHAVIORAL_CAPACITY:
                    del entries[BEHAVIORAL_CAPACITY:]

            else:  # semantic_profile, relationship_map, emotional_sediment
                if o == "write":
                    existing = modules.get(target, "")
                    if existing and existing != "[尚未建立档案]":
                        modules[target] = existing.rstrip() + "\n" + content
                    else:
                        modules[target] = content
                else:
                    modules[target] = content

        # ── note ─────────────────────────────────────────────────────────
        elif o == "note":
            # Memory integrity validation
            safe, reason = validate_entry_integrity(op["content"])
            if not safe:
                print(f"[aether] Note blocked: {reason}", file=sys.stderr)
                continue
            notes: list[dict] = modules.setdefault("notes", [])
            # Deduplicate: skip if very similar raw text already exists
            if not any(op["content"][:20] in n.get("raw", "") for n in notes):
                next_id = max((int(re.search(r"\d+", n["id"]).group()) for n in notes
                               if re.search(r"\d+", n.get("id", ""))), default=0) + 1
                entry = parse_note_entry(op["content"], next_id)
                entry["created_session"] = session
                notes.append(entry)
            if len(notes) > NOTES_CAPACITY:
                del notes[NOTES_CAPACITY:]

        # ── merge ────────────────────────────────────────────────────────
        elif o == "merge":
            ep_list: list[dict] = modules.get("episodic_memory", [])
            merge_ids = set(op["ids"])
            originals = [e for e in ep_list if e["id"] in merge_ids]
            if not originals:
                continue
            # Build merged entry (max importance of originals)
            merged_entry = parse_episodic_entry(op["content"])
            merged_entry["importance"] = max(
                (e.get("importance", 3) for e in originals),
                default=merged_entry["importance"],
            )
            # Remove originals from hot, archive them
            modules["episodic_memory"] = [e for e in ep_list if e["id"] not in merge_ids]
            _archive_entries(d, user_id, memory, originals)
            modules["episodic_memory"].append(merged_entry)
            # Fix behavioral memory source references
            for be in modules.get("behavioral_memory", []):
                sources = be.get("source_ids", [])
                if any(sid.lstrip("#") in merge_ids for sid in sources):
                    be["source_ids"] = [
                        merged_entry["id"] if sid.lstrip("#") in merge_ids else sid
                        for sid in sources
                    ]

        # ── forget ───────────────────────────────────────────────────────
        elif o == "forget":
            target = op["target"]
            if target == "episodic_memory":
                forget_id = op["id"].lstrip("#")
                ep_list = modules.get("episodic_memory", [])
                to_forget = [e for e in ep_list if e["id"] == forget_id]
                modules["episodic_memory"] = [e for e in ep_list if e["id"] != forget_id]
                _archive_entries(d, user_id, memory, to_forget)
                for be in modules.get("behavioral_memory", []):
                    if forget_id in [s.lstrip("#") for s in be.get("source_ids", [])]:
                        be["source_ids"] = [s for s in be["source_ids"] if s.lstrip("#") != forget_id]
                        be["fuzzy_source"] = True
                        be["raw"] = re.sub(r"\(来源[：:][^)]+\)", "(来源已模糊)", be["raw"])

        # ── suppress ─────────────────────────────────────────────────────
        elif o == "suppress":
            if op["target"] == "episodic_memory":
                sid = op["id"].lstrip("#")
                for e in modules.get("episodic_memory", []):
                    if e["id"] == sid:
                        e["suppressed"] = True
                        if "[已压制]" not in e["raw"]:
                            e["raw"] += " [已压制]"
                        break

        # ── SRS: reinforce ───────────────────────────────────────────────
        elif o == "reinforce":
            rid = op["id"]
            for e in modules.get("episodic_memory", []):
                if e["id"] == rid:
                    e["reinforcement_count"] = e.get("reinforcement_count", 0) + 1
                    e["last_reinforced_session"] = session
                    # Reconsolidation: optional reinterpretation note attached to raw
                    if op.get("note"):
                        marker = f" [S{session}重构: {op['note'][:40]}]"
                        # Replace previous reconsolidation note if present
                        e["raw"] = re.sub(r" \[S\d+重构:[^\]]+\]", "", e["raw"]) + marker
                    # Spreading Activation: boost associated memories
                    apply_spreading_activation(
                        modules.get("episodic_memory", []), rid
                    )
                    break

        # ── Associative Memory Network: explicit link ────────────────────
        elif o == "associate":
            ep_list = modules.get("episodic_memory", [])
            link_ids = set(op["ids"])
            for e in ep_list:
                if e["id"] in link_ids:
                    assoc = e.setdefault("associations", [])
                    for other_id in link_ids:
                        if other_id != e["id"] and other_id not in assoc:
                            if len(assoc) < ASSOCIATION_MAX_LINKS:
                                assoc.append(other_id)

        # ── SRS: flashbulb ───────────────────────────────────────────────
        elif o == "flashbulb":
            fid = op["id"]
            for e in modules.get("episodic_memory", []):
                if e["id"] == fid:
                    e["flashbulb"] = True
                    if "[⚡]" not in e["raw"]:
                        # Insert [⚡] after the ID field
                        e["raw"] = re.sub(r"(#e\d+)", r"\1 [⚡]", e["raw"], count=1)
                    break

        # ── Confidence: retract (user correction, highest priority) ──────
        elif o == "retract":
            retract_id = op["id"]
            ep_list = modules.get("episodic_memory", [])
            to_retract = [e for e in ep_list if e["id"] == retract_id]
            if to_retract:
                reason = op.get("reason", "")
                for e in to_retract:
                    tag = f" [已撤销: {reason}]" if reason else " [已撤销]"
                    if "[已撤销]" not in e["raw"]:
                        e["raw"] += tag
                    e["retracted"] = True
                    e["retract_reason"] = reason
                    e["importance"] = 1   # Downgrade so it archives quickly
                modules["episodic_memory"] = [e for e in ep_list if e["id"] != retract_id]
                _archive_entries(d, user_id, memory, to_retract)
                # Also nullify any behavioral patterns sourced from this entry
                for be in modules.get("behavioral_memory", []):
                    if retract_id in [s.lstrip("#") for s in be.get("source_ids", [])]:
                        be["raw"] = re.sub(r"\(来源[：:][^)]+\)", "(来源已撤销)", be["raw"])
                        be["retracted_source"] = True

    # Auto-consolidate fuzzy entries if above threshold
    auto_consolidate(d, user_id, memory)
    return memory


# ---------------------------------------------------------------------------
# XML formatter
# ---------------------------------------------------------------------------

def _ind(text: str, n: int = 4) -> str:
    pad = " " * n
    return "\n".join(pad + ln if ln.strip() else ln for ln in text.splitlines())


# ---------------------------------------------------------------------------
# Capacity-Aware Compaction (inspired by Hermes Agent's capacity management)
# ---------------------------------------------------------------------------

COMPACTION_WARN_THRESHOLD  = 0.75   # Warn when module is ≥75% full
COMPACTION_CRITICAL_THRESHOLD = 0.90  # Critical when ≥90%
SEMANTIC_PROFILE_CHAR_LIMIT = 600
RELATIONSHIP_MAP_CHAR_LIMIT = 400
EMOTIONAL_SEDIMENT_CHAR_LIMIT = 300

# Patterns that suggest prompt injection attempts in memory entries
_INJECTION_PATTERNS = [
    re.compile(r"<\s*/?system", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"<\s*/?prompt", re.IGNORECASE),
    re.compile(r"ANTHROPIC_API_KEY|OPENAI_API_KEY|sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
]


def validate_entry_integrity(text: str) -> tuple[bool, str]:
    """
    Scan memory entry text for injection / exfiltration patterns.
    Returns (is_safe, reason). Inspired by Hermes Agent's security scanning.
    """
    for pat in _INJECTION_PATTERNS:
        if pat.search(text):
            return False, f"Blocked: suspicious pattern detected ({pat.pattern[:30]}…)"
    # Check for invisible Unicode (zero-width chars used for exfiltration)
    invisible = set()
    for ch in text:
        if ord(ch) in (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF) or (0xE0000 <= ord(ch) <= 0xE007F):
            invisible.add(f"U+{ord(ch):04X}")
    if invisible:
        return False, f"Blocked: invisible Unicode characters ({', '.join(invisible)})"
    return True, ""


def compute_capacity_report(memory: dict) -> dict:
    """
    Compute usage percentage for each module.
    Returns {module_name: {used, capacity, pct, status}}.
    """
    modules = memory.get("modules", {})
    report = {}

    # List modules
    ep = modules.get("episodic_memory", [])
    report["episodic_memory"] = {
        "used": len(ep), "capacity": EPISODIC_HOT_CAPACITY,
        "pct": len(ep) / EPISODIC_HOT_CAPACITY if EPISODIC_HOT_CAPACITY else 0,
    }
    bm = modules.get("behavioral_memory", [])
    report["behavioral_memory"] = {
        "used": len(bm), "capacity": BEHAVIORAL_CAPACITY,
        "pct": len(bm) / BEHAVIORAL_CAPACITY if BEHAVIORAL_CAPACITY else 0,
    }
    notes = modules.get("notes", [])
    report["notes"] = {
        "used": len(notes), "capacity": NOTES_CAPACITY,
        "pct": len(notes) / NOTES_CAPACITY if NOTES_CAPACITY else 0,
    }

    # Text modules
    sp = modules.get("semantic_profile", "")
    sp_len = len(sp) if sp != "[尚未建立档案]" else 0
    report["semantic_profile"] = {
        "used": sp_len, "capacity": SEMANTIC_PROFILE_CHAR_LIMIT,
        "pct": sp_len / SEMANTIC_PROFILE_CHAR_LIMIT,
    }
    rm = modules.get("relationship_map", "")
    report["relationship_map"] = {
        "used": len(rm), "capacity": RELATIONSHIP_MAP_CHAR_LIMIT,
        "pct": len(rm) / RELATIONSHIP_MAP_CHAR_LIMIT,
    }
    es = modules.get("emotional_sediment", "")
    report["emotional_sediment"] = {
        "used": len(es), "capacity": EMOTIONAL_SEDIMENT_CHAR_LIMIT,
        "pct": len(es) / EMOTIONAL_SEDIMENT_CHAR_LIMIT,
    }

    # Add status labels
    for v in report.values():
        if v["pct"] >= COMPACTION_CRITICAL_THRESHOLD:
            v["status"] = "CRITICAL"
        elif v["pct"] >= COMPACTION_WARN_THRESHOLD:
            v["status"] = "WARN"
        else:
            v["status"] = "OK"

    return report


def generate_compaction_hints(memory: dict) -> list[str]:
    """
    When modules approach capacity, generate actionable hints for the AI
    to proactively merge/consolidate entries before overflow.
    """
    modules = memory.get("modules", {})
    session = memory.get("session", 0)
    hints = []

    # Episodic: suggest merge candidates (lowest-importance pairs from same session)
    ep = modules.get("episodic_memory", [])
    if len(ep) >= int(EPISODIC_HOT_CAPACITY * COMPACTION_WARN_THRESHOLD):
        # Find low-importance non-protected entries
        sortable = sorted(ep, key=lambda e: effective_importance(e, session))
        weak = [e for e in sortable[:6] if not e.get("flashbulb")]
        if len(weak) >= 2:
            ids = ", ".join(f"#{e['id']}" for e in weak[:3])
            hints.append(
                f"episodic_memory {len(ep)}/{EPISODIC_HOT_CAPACITY} — "
                f"consider <merge> or <forget> low-value entries: {ids}"
            )

    # Behavioral: suggest consolidation
    bm = modules.get("behavioral_memory", [])
    if len(bm) >= int(BEHAVIORAL_CAPACITY * COMPACTION_WARN_THRESHOLD):
        fuzzy = [e for e in bm if e.get("fuzzy_source")]
        if fuzzy:
            hints.append(
                f"behavioral_memory {len(bm)}/{BEHAVIORAL_CAPACITY} — "
                f"{len(fuzzy)} entries have fuzzy sources, consider consolidating"
            )
        else:
            hints.append(
                f"behavioral_memory {len(bm)}/{BEHAVIORAL_CAPACITY} — approaching limit"
            )

    # Notes: warn (notes are permanent, can only merge)
    notes = modules.get("notes", [])
    if len(notes) >= int(NOTES_CAPACITY * COMPACTION_WARN_THRESHOLD):
        hints.append(
            f"notes {len(notes)}/{NOTES_CAPACITY} — "
            f"review for redundant entries that can be merged"
        )

    # Text modules: warn on char limits
    sp = modules.get("semantic_profile", "")
    sp_len = len(sp) if sp != "[尚未建立档案]" else 0
    if sp_len >= int(SEMANTIC_PROFILE_CHAR_LIMIT * COMPACTION_WARN_THRESHOLD):
        hints.append(
            f"semantic_profile {sp_len}/{SEMANTIC_PROFILE_CHAR_LIMIT} chars — "
            f"consider condensing with <update>"
        )

    return hints


def format_memory_load(memory: dict) -> str:
    user_id = memory.get("user_id", "default")
    session = memory.get("session", 0)
    modules = memory.get("modules", {})
    arch = memory.get("archive", {})

    def wrap(tag: str, body: str, attrs: str = "") -> str:
        attr_str = f" {attrs}" if attrs else ""
        return f"  <{tag}{attr_str}>\n{_ind(body)}\n  </{tag}>"

    # Capacity report
    cap = compute_capacity_report(memory)

    def cap_attr(module: str) -> str:
        """Generate capacity attribute string for a module tag."""
        c = cap.get(module, {})
        if not c:
            return ""
        return f'usage="{c["used"]}/{c["capacity"]}" status="{c["status"]}"'

    # Notes
    notes_list = modules.get("notes", [])
    notes_text = "\n".join(
        f"{n['id']}: {n['raw']}" for n in notes_list
    ) if notes_list else "（暂无永久记录）"

    # Episodic
    ep_text = "\n".join(
        e["raw"] for e in modules.get("episodic_memory", [])
    ) or "（暂无记忆）"

    # Behavioral
    bm_text = "\n".join(
        e["raw"] for e in modules.get("behavioral_memory", [])
    ) or "（暂无行为模式）"

    # Archive summary
    summary = arch.get("summary", "")
    count = arch.get("entry_count", 0)
    parts = [
        f'<memory_load session="{session + 1}" previous_session="{session}" user_id="{user_id}">',
        wrap("semantic_profile", modules.get("semantic_profile", "[尚未建立档案]"), cap_attr("semantic_profile")),
        wrap("notes", notes_text, cap_attr("notes")),
        wrap("relationship_map", modules.get(
            "relationship_map",
            "熟悉度: 陌生人\n信任度: 未知\n好感度: 无感\n互动基调: 待观察\n关键转折点: 无",
        ), cap_attr("relationship_map")),
        wrap("episodic_memory", ep_text, cap_attr("episodic_memory")),
        wrap("behavioral_memory", bm_text, cap_attr("behavioral_memory")),
        wrap("emotional_sediment", modules.get(
            "emotional_sediment", "新的对话。新的人。保持距离，先观察。"
        ), cap_attr("emotional_sediment")),
    ]
    if count > 0 or summary:
        arch_body = summary if summary else f"归档记忆 {count} 条。"
        sa = arch.get("sessions_archived", 0)
        parts.append(
            f'  <memory_archive sessions_archived="{sa}" total="{count}">\n'
            f'{_ind(arch_body)}\n'
            f'  </memory_archive>'
        )

    # Compaction hints — only when modules are getting full
    hints = generate_compaction_hints(memory)
    if hints:
        hints_body = "\n".join(f"• {h}" for h in hints)
        parts.append(
            f'  <compaction_hints>\n{_ind(hints_body)}\n  </compaction_hints>'
        )

    parts.append("</memory_load>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# First-run init block
# ---------------------------------------------------------------------------

def format_memory_init(user_id: str) -> str:
    """
    Output when no memory file exists yet.  Tells the AI to ask the user for
    their preferred ID (and any initial facts) before the session begins.
    """
    if user_id == "default":
        instruction = (
            "以太尚未绑定用户身份。请向用户说明情况并询问：\n"
            "  1. 你希望用什么标识符保存记忆？（昵称、英文名均可，例如 alice / 小陈）\n"
            "  2. 有没有你希望我初始就记住的信息？（可选）\n\n"
            "获取用户回答后，依次执行：\n"
            "  a. python3 \"${CLAUDE_SKILL_DIR}/scripts/aether.py\" init <user_id>\n"
            "  b. python3 \"${CLAUDE_SKILL_DIR}/scripts/aether.py\" load <user_id>\n"
            "  c. 将步骤 b 的输出作为新的记忆状态，此后所有操作使用该 user_id。\n"
            "  d. 如果用户提供了初始信息，立刻用 <mem_ops> 写入 semantic_profile。"
        )
    else:
        instruction = (
            f"用户 '{user_id}' 的记忆文件尚不存在，这是与该用户的第一次对话。\n"
            f"已注入空白记忆。对话结束时请运行：\n"
            f"  python3 \"${{CLAUDE_SKILL_DIR}}/scripts/aether.py\" save {user_id}"
        )
    return (
        f'<memory_init user_id="{user_id}" first_run="true">\n'
        f'{_ind(instruction)}\n'
        f'</memory_init>'
    )


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_load(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    is_new = not memory_path(d, user_id).exists()
    memory = load_memory(d, user_id)
    if getattr(args, "json", False):
        print(json.dumps(memory, ensure_ascii=False, indent=2))
        return
    print(format_memory_load(memory))
    if is_new:
        print(format_memory_init(user_id))


def cmd_save(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    text = sys.stdin.read()
    modules, session = parse_snapshot(text)
    if modules is None:
        print("[aether] Error: no <memory_snapshot> found in input.", file=sys.stderr)
        sys.exit(1)
    memory = load_memory(d, user_id)
    memory["modules"].update(modules)
    memory["session"] = session if session is not None else memory.get("session", 0) + 1
    track_relationship(memory)
    save_memory(d, user_id, memory)
    print(f"[aether] Saved '{user_id}' → session {memory['session']}")


def cmd_apply(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    text = sys.stdin.read()
    ops = parse_mem_ops(text)
    if not ops:
        if args.verbose:
            print("[aether] No <mem_ops> found.", file=sys.stderr)
        return
    memory = load_memory(d, user_id)
    apply_ops(d, user_id, memory, ops)
    save_memory(d, user_id, memory)
    if args.verbose:
        print(f"[aether] Applied {len(ops)} op(s) to '{user_id}':", file=sys.stderr)
        for op in ops:
            print(f"  {op['op']:10s} → {op.get('target', op.get('ids', ''))}", file=sys.stderr)


def cmd_init(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    path = memory_path(d, user_id)
    if path.exists() and not args.force:
        print(f"[aether] '{user_id}' already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)
    memory = json.loads(json.dumps(BLANK_MEMORY))
    memory["user_id"] = user_id
    save_memory(d, user_id, memory)
    print(f"[aether] Initialized blank memory for '{user_id}'.", file=sys.stderr)
    print(format_memory_load(memory))


def cmd_status(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    memory = load_memory(d, user_id)
    modules = memory.get("modules", {})
    ep = modules.get("episodic_memory", [])
    bm = modules.get("behavioral_memory", [])
    notes = modules.get("notes", [])
    arch = memory.get("archive", {})

    print(f"User           : {user_id}")
    print(f"Session        : {memory.get('session', 0)}")
    print(f"Last updated   : {(memory.get('last_updated') or 'never')[:19]}")
    session = memory.get("session", 0)
    print(f"Episodic (hot) : {len(ep)}/{EPISODIC_HOT_CAPACITY}"
          f"  [suppressed={sum(1 for e in ep if e.get('suppressed'))}"
          f"  fuzzy={sum(1 for e in ep if e.get('fuzzy'))}"
          f"  flashbulb={sum(1 for e in ep if e.get('flashbulb'))}]")
    if ep:
        dist: dict[int, int] = {}
        for e in ep:
            k = e.get("importance", 3)
            dist[k] = dist.get(k, 0) + 1
        print("  ★-dist : " + "  ".join(f"{'★'*k}:{v}" for k, v in sorted(dist.items())))
        # SRS stats
        reinforced = [(e["id"], e.get("reinforcement_count", 0))
                      for e in ep if e.get("reinforcement_count", 0) > 0]
        if reinforced:
            reinforced.sort(key=lambda x: -x[1])
            top3 = "  ".join(f"#{i}×{c}" for i, c in reinforced[:3])
            print(f"  SRS top : {top3}")
        eff_scores = [(e["id"], effective_importance(e, session)) for e in ep]
        eff_scores.sort(key=lambda x: -x[1])
        top3_eff = "  ".join(f"#{i}={s:.1f}" for i, s in eff_scores[:3])
        print(f"  Eff.imp : {top3_eff}")
    # Association network stats
    assoc_links = sum(len(e.get("associations", [])) for e in ep)
    assoc_boosted = sum(1 for e in ep if e.get("association_boost", 0) > 0)
    if assoc_links > 0 or assoc_boosted > 0:
        print(f"  Assoc.  : {assoc_links} links, {assoc_boosted} entries boosted")
    print(f"Behavioral     : {len(bm)}/{BEHAVIORAL_CAPACITY}")
    print(f"Notes          : {len(notes)}/{NOTES_CAPACITY}")
    print(f"Archive        : {arch.get('entry_count', 0)} entries"
          f"  (sessions archived: {arch.get('sessions_archived', 0)})")
    sp = modules.get("semantic_profile", "")
    print(f"Semantic       : {len(sp)} chars" if sp != "[尚未建立档案]" else "Semantic       : (not established)")
    arc = arch.get("relationship_arc", [])
    if arc:
        arc_str = " → ".join(f"S{a['session']}:{a['familiarity']}" for a in arc[-4:])
        print(f"Rel. arc       : {arc_str}")


def cmd_list(args: argparse.Namespace, d: Path) -> None:
    files = sorted(f for f in d.glob("*.json") if not re.search(r"\.s\d{3}\.json$", f.name))
    if not files:
        print(f"[aether] No memory files in {d}")
        return
    print(f"{'User':<20} {'Sess':>4}  {'Hot':>4}  {'Notes':>5}  {'Arch':>5}  Updated")
    print("-" * 65)
    for path in files:
        uid = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            sess = data.get("session", 0)
            ep = len(data.get("modules", {}).get("episodic_memory", []))
            nt = len(data.get("modules", {}).get("notes", []))
            ar = data.get("archive", {}).get("entry_count", 0)
            upd = (data.get("last_updated") or "unknown")[:10]
            print(f"{uid:<20} {sess:>4}  {ep:>4}  {nt:>5}  {ar:>5}  {upd}")
        except (json.JSONDecodeError, OSError):
            print(f"{uid:<20}  (corrupted)")


def cmd_history(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    prefix = _safe(user_id)
    backups = sorted(d.glob(f"{prefix}.s*.json"))
    if not backups:
        print(f"[aether] No session backups found for '{user_id}'.")
        return
    print(f"Session history for '{user_id}':")
    print(f"  {'File':<30}  {'Session':>7}  {'Hot':>4}  Date")
    print("  " + "-" * 55)
    for path in backups:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            sess = data.get("session", "?")
            ep = len(data.get("modules", {}).get("episodic_memory", []))
            upd = (data.get("last_updated") or "unknown")[:10]
            print(f"  {path.name:<30}  {sess:>7}  {ep:>4}  {upd}")
        except (json.JSONDecodeError, OSError):
            print(f"  {path.name:<30}  (corrupted)")


def cmd_consolidate(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    memory = load_memory(d, user_id)
    modules = memory.get("modules", {})
    ep = modules.get("episodic_memory", [])

    # Archive ALL fuzzy entries, regardless of count
    fuzzy = [e for e in ep if e.get("fuzzy")]
    if fuzzy:
        fuzzy_ids = {e["id"] for e in fuzzy}
        modules["episodic_memory"] = [e for e in ep if e["id"] not in fuzzy_ids]
        _archive_entries(d, user_id, memory, fuzzy)
        print(f"[aether] Archived {len(fuzzy)} fuzzy entr(ies) for '{user_id}'.")
    else:
        print(f"[aether] No fuzzy entries to consolidate for '{user_id}'.")

    # Track relationship and rebuild summary
    track_relationship(memory)
    all_archived = load_archive_entries(d, user_id)
    arch = memory.setdefault("archive", {})
    arch["entry_count"] = len(all_archived)
    arch["summary"] = build_archive_summary(all_archived, arch.get("relationship_arc", []))
    arch["sessions_archived"] = memory.get("session", 0)
    save_memory(d, user_id, memory)
    print(f"[aether] Archive total: {arch['entry_count']} entries. Summary rebuilt.")


def cmd_forget(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    if not args.id:
        print("[aether] Error: --id required for forget.", file=sys.stderr)
        sys.exit(1)
    memory = load_memory(d, user_id)
    apply_ops(d, user_id, memory, [{"op": "forget", "target": "episodic_memory",
                                    "id": args.id, "reason": "explicit"}])
    save_memory(d, user_id, memory)
    print(f"[aether] Entry '{args.id}' moved to archive for '{user_id}'.")


def cmd_prune(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    memory = load_memory(d, user_id)
    modules = memory.get("modules", {})
    ep = modules.get("episodic_memory", [])
    # Archive fuzzy + suppressed low-importance entries
    to_archive = [
        e for e in ep
        if e.get("fuzzy") or (e.get("suppressed") and e.get("importance", 3) <= 2)
    ]
    if to_archive:
        archive_ids = {e["id"] for e in to_archive}
        modules["episodic_memory"] = [e for e in ep if e["id"] not in archive_ids]
        _archive_entries(d, user_id, memory, to_archive)
    save_memory(d, user_id, memory)
    print(f"[aether] Archived {len(to_archive)} entr(ies) for '{user_id}'. "
          f"Hot remaining: {len(modules['episodic_memory'])}")


def cmd_recall(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    keywords = [k.lower() for k in (args.keywords or [])]
    if not keywords:
        print("[aether] Error: provide at least one keyword to search.", file=sys.stderr)
        sys.exit(1)
    entries = load_archive_entries(d, user_id)
    if not entries:
        print(f"[aether] No archive for '{user_id}'.")
        return
    results = [
        e for e in entries
        if all(k in e.get("raw", "").lower() for k in keywords)
    ]
    if not results:
        print(f"[aether] No matches for: {' '.join(keywords)}")
        return
    print(f"Found {len(results)} match(es) in archive for '{user_id}':")
    for e in results:
        sess = e.get("archived_session", "?")
        print(f"  [S{sess}] {e.get('raw', '')}")


def cmd_export(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    memory = load_memory(d, user_id)
    archive_entries = load_archive_entries(d, user_id)
    export = {
        "hot": memory,
        "archive_entries": archive_entries,
        "exported_at": datetime.now().isoformat(),
    }
    print(json.dumps(export, ensure_ascii=False, indent=2))


def cmd_drift(args: argparse.Namespace, d: Path) -> None:
    """Emotional trajectory analysis — track how the relationship evolves."""
    user_id = args.user_id or "default"
    memory = load_memory(d, user_id)
    modules = memory.get("modules", {})
    ep = modules.get("episodic_memory", [])
    archive = load_archive_entries(d, user_id)
    all_entries = ep + archive

    if not all_entries:
        print(f"[aether] No memories to analyze for '{user_id}'.")
        return

    # Group by session
    sessions: dict[int, list[dict]] = {}
    for e in all_entries:
        s = e.get("first_session") or e.get("archived_session") or 0
        sessions.setdefault(s, []).append(e)

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║  Emotional Drift Analysis — {user_id:<20s} ║")
    print(f"╠══════════════════════════════════════════════════╣")

    # Per-session emotional analysis
    for s in sorted(sessions.keys()):
        entries = sessions[s]
        pos = sum(1 for e in entries if _extract_emotion_class(e.get("raw", "")) == "positive")
        neg = sum(1 for e in entries if _extract_emotion_class(e.get("raw", "")) == "negative")
        total = len(entries)
        avg_imp = sum(e.get("importance", 3) for e in entries) / total if total else 0

        # Visual bar
        bar_len = 20
        if total > 0:
            pos_bar = int(pos / total * bar_len)
            neg_bar = int(neg / total * bar_len)
            neu_bar = bar_len - pos_bar - neg_bar
        else:
            pos_bar = neg_bar = 0
            neu_bar = bar_len
        bar = "█" * pos_bar + "░" * neu_bar + "▓" * neg_bar

        print(f"║  S{s:<3d} [{bar}] {total:>2d}条  avg★{avg_imp:.1f}  +{pos}/-{neg}  ║")

    # Relationship arc
    arc = memory.get("archive", {}).get("relationship_arc", [])
    if arc:
        print(f"╠══════════════════════════════════════════════════╣")
        arc_str = " → ".join(f"S{a['session']}:{a['familiarity']}" for a in arc)
        # Wrap long arcs
        while len(arc_str) > 46:
            print(f"║  {arc_str[:46]}  ║")
            arc_str = arc_str[46:]
        print(f"║  {arc_str:<46s}  ║")

    # Association network stats
    assoc_count = sum(len(e.get("associations", [])) for e in ep)
    boosted = sum(1 for e in ep if e.get("association_boost", 0) > 0)
    if assoc_count > 0 or boosted > 0:
        print(f"╠══════════════════════════════════════════════════╣")
        print(f"║  Association Network: {assoc_count} links, {boosted} boosted   ║")

    print(f"╚══════════════════════════════════════════════════╝")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aether",
        description="Aether Memory System v3.0 — two-tier persistent memory for AI personas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("command", choices=[
        "load", "save", "apply", "init", "status", "list",
        "history", "consolidate", "forget", "prune", "recall", "export",
        "drift",
    ])
    p.add_argument("user_id", nargs="?", default=None)
    p.add_argument("keywords", nargs="*", help="Keywords for recall command")
    p.add_argument("--dir", default=None)
    p.add_argument("--id", default=None, help="Entry ID (forget)")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main() -> None:
    # parse_known_args so that extra positionals for `recall` aren't rejected
    args, extras = build_parser().parse_known_args()
    if args.command == "recall" and extras:
        args.keywords = list(args.keywords or []) + [e for e in extras if not e.startswith("-")]
    elif extras:
        build_parser().error(f"unrecognized arguments: {' '.join(extras)}")
    d = resolve_dir(args.dir)
    {
        "load":        cmd_load,
        "save":        cmd_save,
        "apply":       cmd_apply,
        "init":        cmd_init,
        "status":      cmd_status,
        "list":        cmd_list,
        "history":     cmd_history,
        "consolidate": cmd_consolidate,
        "forget":      cmd_forget,
        "prune":       cmd_prune,
        "recall":      cmd_recall,
        "export":      cmd_export,
        "drift":       cmd_drift,
    }[args.command](args, d)


if __name__ == "__main__":
    main()
