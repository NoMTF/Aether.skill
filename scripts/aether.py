#!/usr/bin/env python3
"""
Aether Memory System — Backend Script
以太记忆系统 · 后端存储层

Manages persistent memory files for AI persona sessions. Reads and writes
structured JSON on disk; emits XML-format <memory_load> blocks for context
injection; parses <mem_ops> / <memory_snapshot> from assistant responses.

Commands:
  load    [user_id]           Load memory → print <memory_load> XML
  save    [user_id]           Read <memory_snapshot> from stdin → persist
  apply   [user_id]           Read assistant text from stdin → apply <mem_ops>
  init    [user_id]           Create a blank memory file (first-time setup)
  status  [user_id]           Print memory statistics
  list                        List all users with saved memories
  forget  [user_id] --id ID   Remove a single episodic entry
  prune   [user_id]           Remove fuzzy / suppressed low-importance entries

Options:
  --dir DIR      Override memory storage directory
  --force        Allow overwriting existing memory (init command)
  --json         Output raw JSON instead of XML (load command)
  -v, --verbose  Print extra info to stderr
"""

import sys
import os
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Storage layout
# ---------------------------------------------------------------------------

DEFAULT_DIRS = [
    Path(".aether") / "memories",
    Path.home() / ".aether" / "memories",
]

BLANK_MEMORY = {
    "user_id": "default",
    "session": 0,
    "last_updated": None,
    "modules": {
        "semantic_profile": "[尚未建立档案]",
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
}

EPISODIC_CAPACITY = 30
BEHAVIORAL_CAPACITY = 25


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def resolve_dir(dir_arg: str | None) -> Path:
    if dir_arg:
        d = Path(dir_arg)
    else:
        d = next((p for p in DEFAULT_DIRS if p.exists()), DEFAULT_DIRS[0])
    d.mkdir(parents=True, exist_ok=True)
    return d


def memory_path(d: Path, user_id: str) -> Path:
    # Sanitise: only allow safe filename characters
    safe = re.sub(r"[^\w\-.]", "_", user_id)
    return d / f"{safe}.json"


# ---------------------------------------------------------------------------
# JSON load / save
# ---------------------------------------------------------------------------

def load_memory(d: Path, user_id: str) -> dict:
    path = memory_path(d, user_id)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[aether] Warning: could not read {path}: {e}", file=sys.stderr)
    mem = json.loads(json.dumps(BLANK_MEMORY))  # deep copy
    mem["user_id"] = user_id
    return mem


def save_memory(d: Path, user_id: str, memory: dict) -> None:
    path = memory_path(d, user_id)
    # Write a session-numbered backup before overwriting
    session = memory.get("session", 0)
    if path.exists() and session > 0:
        backup = d / f"{path.stem}.s{session:03d}.json"
        try:
            with open(backup, "w", encoding="utf-8") as f:
                with open(path, encoding="utf-8") as src:
                    f.write(src.read())
        except OSError:
            pass  # Backup failure is non-fatal
    memory["last_updated"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_importance(stars_text: str) -> int:
    """Count filled stars (★) in a string, clamp to 1–5."""
    return max(1, min(5, stars_text.count("★")))


def parse_episodic_entry(raw: str) -> dict:
    """
    Parse one episodic memory line.
    Expected format: #eNN ★★★☆☆ 😊 时间锚点 | summary
    """
    raw = raw.strip()
    m = re.match(r"(#e\d+)\s+((?:★|☆)+)\s+(.+?)\s+(.+?)\s*\|\s*(.+)", raw)
    if m:
        return {
            "id": m.group(1).lstrip("#"),
            "raw": raw,
            "importance": parse_importance(m.group(2)),
            "suppressed": False,
            "fuzzy": "[模糊]" in raw,
        }
    # Fallback: keep as-is, assume medium importance
    id_m = re.match(r"#(e\d+)", raw)
    return {
        "id": id_m.group(1) if id_m else "e??",
        "raw": raw,
        "importance": 3,
        "suppressed": "[已压制]" in raw,
        "fuzzy": "[模糊]" in raw,
    }


def parse_behavioral_entry(raw: str) -> dict:
    raw = raw.strip()
    source_ids = [f"e{s}" for s in re.findall(r"#e(\d+)", raw)]
    return {
        "raw": raw,
        "source_ids": source_ids,
        "fuzzy_source": "[来源已模糊]" in raw,
    }


def parse_mem_ops(text: str) -> list[dict]:
    """Extract all <mem_ops> blocks and return a flat list of operation dicts."""
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
    return ops


def parse_snapshot(text: str) -> tuple[dict | None, int | None]:
    """
    Parse a <memory_snapshot session="N">...</memory_snapshot> block.
    Returns (modules_dict, session_number) or (None, None) if not found.
    """
    snap_m = re.search(
        r'<memory_snapshot(?:\s+session="(\d+)")?[^>]*>(.*?)</memory_snapshot>',
        text,
        re.DOTALL,
    )
    if not snap_m:
        return None, None

    session = int(snap_m.group(1)) if snap_m.group(1) else None
    body = snap_m.group(2)
    modules: dict = {}

    for mod in [
        "semantic_profile",
        "relationship_map",
        "episodic_memory",
        "behavioral_memory",
        "emotional_sediment",
    ]:
        m = re.search(rf"<{mod}>(.*?)</{mod}>", body, re.DOTALL)
        if not m:
            continue
        # Strip per-line indentation that may come from snapshot XML formatting
        content = "\n".join(line.strip() for line in m.group(1).splitlines()).strip()
        if mod == "episodic_memory":
            entries = [
                parse_episodic_entry(line)
                for line in content.splitlines()
                if line.strip().startswith("#e")
            ]
            modules[mod] = entries
        elif mod == "behavioral_memory":
            entries = [
                parse_behavioral_entry(line)
                for line in content.splitlines()
                if line.strip()
            ]
            modules[mod] = entries
        else:
            modules[mod] = content

    return modules, session


# ---------------------------------------------------------------------------
# Memory operations
# ---------------------------------------------------------------------------

def apply_ops(memory: dict, ops: list[dict]) -> dict:
    """Mutate memory in-place by applying the given ops list, return memory."""
    modules = memory.setdefault("modules", {})

    for op in ops:
        target = op["target"]
        o = op["op"]

        if o in ("write", "update"):
            content = op["content"]

            if target == "episodic_memory":
                entries: list[dict] = modules.setdefault("episodic_memory", [])
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    entry = parse_episodic_entry(line)
                    existing = next((e for e in entries if e["id"] == entry["id"]), None)
                    if existing and o == "update":
                        existing.update(entry)
                    else:
                        entries.append(entry)
                # Enforce capacity: sort by importance desc, remove tail
                if len(entries) > EPISODIC_CAPACITY:
                    entries.sort(key=lambda e: (
                        -e.get("importance", 3),
                        e.get("fuzzy", False),
                        e.get("suppressed", False),
                    ))
                    del entries[EPISODIC_CAPACITY:]

            elif target == "behavioral_memory":
                entries = modules.setdefault("behavioral_memory", [])
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        entries.append(parse_behavioral_entry(line))
                if len(entries) > BEHAVIORAL_CAPACITY:
                    del entries[BEHAVIORAL_CAPACITY:]

            else:
                # Text modules: semantic_profile, relationship_map, emotional_sediment
                if o == "write":
                    existing = modules.get(target, "")
                    if existing and existing != "[尚未建立档案]":
                        modules[target] = existing.rstrip() + "\n" + content
                    else:
                        modules[target] = content
                else:  # update → full replace
                    modules[target] = content

        elif o == "forget":
            if target == "episodic_memory":
                entries = modules.get("episodic_memory", [])
                forget_id = op["id"].lstrip("#")
                modules["episodic_memory"] = [
                    e for e in entries if e["id"] != forget_id
                ]
                # Mark dependent behavioral entries as fuzzy-sourced
                for be in modules.get("behavioral_memory", []):
                    if forget_id in [s.lstrip("#") for s in be.get("source_ids", [])]:
                        be["source_ids"] = [
                            s for s in be["source_ids"] if s.lstrip("#") != forget_id
                        ]
                        be["fuzzy_source"] = True
                        be["raw"] = re.sub(
                            r"\(来源[：:][^)]+\)",
                            "(来源已模糊)",
                            be["raw"],
                        )

        elif o == "suppress":
            if target == "episodic_memory":
                suppress_id = op["id"].lstrip("#")
                for e in modules.get("episodic_memory", []):
                    if e["id"] == suppress_id:
                        e["suppressed"] = True
                        if "[已压制]" not in e["raw"]:
                            e["raw"] += " [已压制]"
                        break

    return memory


# ---------------------------------------------------------------------------
# XML formatter
# ---------------------------------------------------------------------------

def indent(text: str, n: int = 4) -> str:
    pad = " " * n
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


def format_memory_load(memory: dict) -> str:
    user_id = memory.get("user_id", "default")
    session = memory.get("session", 0)
    modules = memory.get("modules", {})

    def wrap(tag: str, body: str) -> str:
        return f"  <{tag}>\n{indent(body)}\n  </{tag}>"

    # Episodic list → text
    episodic_lines: list[str] = []
    for e in modules.get("episodic_memory", []):
        episodic_lines.append(e.get("raw", ""))
    episodic_text = "\n".join(episodic_lines) if episodic_lines else "（暂无记忆）"

    # Behavioral list → text
    behavioral_lines = [e.get("raw", "") for e in modules.get("behavioral_memory", [])]
    behavioral_text = "\n".join(behavioral_lines) if behavioral_lines else "（暂无行为模式）"

    parts = [
        f'<memory_load session="{session + 1}" previous_session="{session}" user_id="{user_id}">',
        wrap("semantic_profile", modules.get("semantic_profile", "[尚未建立档案]")),
        wrap("relationship_map", modules.get(
            "relationship_map",
            "熟悉度: 陌生人\n信任度: 未知\n好感度: 无感\n互动基调: 待观察\n关键转折点: 无",
        )),
        wrap("episodic_memory", episodic_text),
        wrap("behavioral_memory", behavioral_text),
        wrap("emotional_sediment", modules.get(
            "emotional_sediment", "新的对话。新的人。保持距离，先观察。"
        )),
        "</memory_load>",
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_load(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    memory = load_memory(d, user_id)
    if args.json:
        print(json.dumps(memory, ensure_ascii=False, indent=2))
    else:
        print(format_memory_load(memory))


def cmd_save(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    text = sys.stdin.read()
    modules, session = parse_snapshot(text)
    if modules is None:
        print("[aether] Error: no <memory_snapshot> found in input.", file=sys.stderr)
        sys.exit(1)
    memory = load_memory(d, user_id)
    memory["modules"].update(modules)
    if session is not None:
        memory["session"] = session
    else:
        memory["session"] = memory.get("session", 0) + 1
    save_memory(d, user_id, memory)
    print(f"[aether] Saved memory for '{user_id}' → session {memory['session']}")


def cmd_apply(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    text = sys.stdin.read()
    ops = parse_mem_ops(text)
    if not ops:
        if args.verbose:
            print("[aether] No <mem_ops> found in input.", file=sys.stderr)
        return
    memory = load_memory(d, user_id)
    apply_ops(memory, ops)
    save_memory(d, user_id, memory)
    if args.verbose:
        print(f"[aether] Applied {len(ops)} op(s) to '{user_id}':", file=sys.stderr)
        for op in ops:
            print(f"  {op['op']:8s} → {op['target']}", file=sys.stderr)


def cmd_init(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    path = memory_path(d, user_id)
    if path.exists() and not args.force:
        print(
            f"[aether] Memory for '{user_id}' already exists. "
            "Use --force to overwrite.",
            file=sys.stderr,
        )
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

    print(f"User        : {user_id}")
    print(f"Session     : {memory.get('session', 0)}")
    print(f"Last updated: {memory.get('last_updated', 'never')}")
    print(f"Episodic    : {len(ep)}/{EPISODIC_CAPACITY}")
    suppressed = sum(1 for e in ep if e.get("suppressed"))
    fuzzy = sum(1 for e in ep if e.get("fuzzy"))
    if suppressed or fuzzy:
        print(f"  suppressed={suppressed}  fuzzy={fuzzy}")
    if ep:
        dist: dict[int, int] = {}
        for e in ep:
            k = e.get("importance", 3)
            dist[k] = dist.get(k, 0) + 1
        print("  importance: " + "  ".join(f"★×{k}:{v}" for k, v in sorted(dist.items())))
    print(f"Behavioral  : {len(bm)}/{BEHAVIORAL_CAPACITY}")
    sp = modules.get("semantic_profile", "")
    if sp and sp != "[尚未建立档案]":
        print(f"Semantic    : {len(sp)} chars")
    else:
        print("Semantic    : (not yet established)")


def cmd_list(args: argparse.Namespace, d: Path) -> None:
    files = sorted(
        f for f in d.glob("*.json")
        if not re.search(r"\.s\d{3}\.json$", f.name)
    )
    if not files:
        print(f"[aether] No memory files in {d}")
        return
    print(f"{'User':<20} {'Session':>7}  {'Memories':>8}  Last updated")
    print("-" * 58)
    for path in files:
        uid = path.stem
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            sess = data.get("session", 0)
            ep = len(data.get("modules", {}).get("episodic_memory", []))
            upd = (data.get("last_updated") or "unknown")[:10]
            print(f"{uid:<20} {sess:>7}  {ep:>8}  {upd}")
        except (json.JSONDecodeError, OSError):
            print(f"{uid:<20}  (corrupted)")


def cmd_forget(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    if not args.id:
        print("[aether] Error: --id required for forget command.", file=sys.stderr)
        sys.exit(1)
    memory = load_memory(d, user_id)
    apply_ops(memory, [{"op": "forget", "target": "episodic_memory", "id": args.id, "reason": "explicit"}])
    save_memory(d, user_id, memory)
    print(f"[aether] Forgot entry '{args.id}' for '{user_id}'.")


def cmd_prune(args: argparse.Namespace, d: Path) -> None:
    user_id = args.user_id or "default"
    memory = load_memory(d, user_id)
    modules = memory.get("modules", {})
    ep = modules.get("episodic_memory", [])
    before = len(ep)
    ep = [
        e for e in ep
        if not (
            e.get("fuzzy")
            or (e.get("suppressed") and e.get("importance", 3) <= 2)
        )
    ]
    modules["episodic_memory"] = ep
    save_memory(d, user_id, memory)
    print(f"[aether] Pruned {before - len(ep)} entr(ies) for '{user_id}'. Remaining: {len(ep)}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aether",
        description="Aether Memory System — persistent memory backend for AI personas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "command",
        choices=["load", "save", "apply", "init", "status", "list", "forget", "prune"],
    )
    p.add_argument("user_id", nargs="?", default=None, help="User identifier (default: 'default')")
    p.add_argument("--dir", default=None, help="Memory storage directory")
    p.add_argument("--id", default=None, help="Episodic entry ID for forget/suppress commands")
    p.add_argument("--force", action="store_true", help="Overwrite existing memory (init)")
    p.add_argument("--json", action="store_true", help="Output raw JSON (load)")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose stderr output")
    return p


def main() -> None:
    args = build_parser().parse_args()
    d = resolve_dir(args.dir)

    dispatch = {
        "load": cmd_load,
        "save": cmd_save,
        "apply": cmd_apply,
        "init": cmd_init,
        "status": cmd_status,
        "list": cmd_list,
        "forget": cmd_forget,
        "prune": cmd_prune,
    }
    dispatch[args.command](args, d)


if __name__ == "__main__":
    main()
