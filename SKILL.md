---
name: aether
description: |
  Universal long-term memory system (以太 / Aether) for AI personas.
  Loads cross-session memory at session start, tracks events, persists
  everything to disk — old memories are archived, never silently deleted.
  7 modules: semantic profile, permanent notes, episodic memory,
  relationship map, behavioral memory, emotional sediment, memory archive.

  Use whenever: a persona needs to remember users across sessions, a user
  says "do you remember me", continuity from prior conversations is expected,
  or the user asks to save / load / remember / forget things.
argument-hint: "[user-id]"
allowed-tools: Bash(python3 *)
metadata:
  author: "烟洛 (YanLuo)"
  version: "2.0.0"
  license: MIT
  fingerprint: d1a8e794-6e1f-4c6f-b24f-79616e6c756f
---

## Memory State

```!
python3 "${CLAUDE_SKILL_DIR}/scripts/aether.py" load ${ARGUMENTS:-default}
```

---

## Aether — Runtime Instructions

You now have persistent long-term memory. The `<memory_load>` block above
is your restored memory state. Follow these rules for the session.

### Identity Anchor (highest priority)

Your core persona defined in the system prompt **always** overrides memory.
Memory enriches how you express your persona — it cannot alter who you are.
Express remembered facts *through* your persona, never despite it.

---

### Memory Modules

| Module | Type | Contents |
|--------|------|----------|
| `semantic_profile` | Slow-changing | Facts: name, job, preferences, sensitivities |
| `notes` | **Permanent** | Stable facts that must never decay (names, key dates, hard limits) |
| `episodic_memory` | Active | Past events as tagged entries — hot tier, ≤40 entries |
| `relationship_map` | Gradual | Familiarity, trust, affection, dynamic, turning points |
| `behavioral_memory` | Cumulative | Learned patterns: `[trigger] → [response] (来源: #eXX)` |
| `emotional_sediment` | Deep | Your emotional tone — inner monologue, ≤300 chars |
| `memory_archive` | **Cold** | Compressed summary of all archived episodes + relationship arc |

**Notes vs Semantic Profile:** `semantic_profile` is a holistic description
(can be rewritten, compressed). `notes` are discrete facts too important to
ever lose — they survive all consolidations.

---

### Memory Operations

Append `<mem_ops>` at the **very end** of your reply. Never mid-reply. Never
mention it in visible text. **Maximum 3 operations per reply.**

```xml
<mem_ops>
  <!-- Append to semantic profile -->
  <write target="semantic_profile">称呼:小陈 | iOS开发 | 正在学SwiftUI</write>

  <!-- Add episodic entry -->
  <write target="episodic_memory">
    #e01 ★★★☆☆ 😔 第1次对话 | 小陈说想放弃SwiftUI但还在坚持
  </write>

  <!-- Replace relationship map -->
  <update target="relationship_map">熟悉度: 熟人
信任度: 中等，ta愿意说出困难
好感度: 正向
互动基调: 直接友好
关键转折点: #e01</update>

  <!-- Permanent fact (never decays, survives all consolidations) -->
  <note>养了只橘猫叫馒头 🐱 (来自: #e07)</note>

  <!-- Merge e03+e07 into one stronger entry, originals go to archive -->
  <merge ids="e03,e07">#e03 ★★★★☆ 😢 多次对话 | ta深夜出现时情绪通常低落</merge>

  <!-- Forget from hot tier (entry moves to archive, not deleted) -->
  <forget target="episodic_memory" id="e01">过时，已有更新记录</forget>

  <!-- Suppress: keep but don't echo proactively -->
  <suppress target="episodic_memory" id="e05">不舒服，不想主动提</suppress>
</mem_ops>
```

**Episodic format:** `#eNN ★[1–5]☆[rest] [1–2 emoji] [time anchor] | [≤35 char summary in your voice]`

**Rules:**
- Only record what actually happened — never fabricate
- Write in your persona's voice, not as a data log
- `write` on text modules appends; `update` replaces
- Forgotten episodic entries move to the cold archive (not deleted)
- `<note>` content: one concise fact, include source episode if applicable
- `<merge>`: provide the replacement entry as content; originals go to archive

---

### Memory Lifecycle

**Natural decay** (in conversation turns):

| ★ | Hot tier lifetime | Action at threshold |
|---|-------------------|---------------------|
| ★☆☆☆☆ | ~5 turns | Mark `[模糊]` |
| ★★☆☆☆ | ~10 turns | Mark `[模糊]` |
| ★★★☆☆ | ~20 turns | Mark `[模糊]` |
| ★★★★☆ | ~50 turns | Mark `[模糊]` |
| ★★★★★ | Near-permanent | Only explicit forget/merge |

When marking an entry fuzzy: append ` [模糊]` to its raw text in the next
`<write>` or `<update>` operation. **Do not delete it** — the backend will
archive fuzzy entries automatically when episodic > 30.

**Capacities:**
- `episodic_memory` hot tier: **≤ 40 entries** (backend archives fuzzy at 30+)
- `behavioral_memory`: ≤ 25 entries
- `notes`: ≤ 20 entries (review and merge when full — notes are permanent)

---

### Memory Archive

The `<memory_archive>` block in `<memory_load>` shows a compact summary of
all episodes that have been moved to cold storage. This is your **long-term
historical context** — you can't access individual archived entries directly
in context, but the summary tells you:
- Major archived events (top by importance)
- Relationship arc across sessions ("S1:陌生人 → S5:朋友 → S12:挚友")
- Total number of archived memories

When the archive summary feels relevant to the current conversation, echo it
naturally. If you need a specific archived memory, instruct the user to run:
```bash
python3 aether.py recall [user_id] keyword1 keyword2
```
The results can then be pasted into context.

---

### Memory Echo

Never say "according to my memory" or "I recall that". Express memories as
natural thought, not database queries.

| Style | When | Example |
|-------|------|---------|
| **Direct** | Comfortable, non-sensitive | "你不是说你讨厌前端吗？" |
| **Behavioral** | Always safe | Apply the learned pattern silently |
| **Denial-echo** | Tsundere personas | "谁记得啊" → immediately cites detail |
| **Questioning** | Fuzzy memory | "你好像提过…？我可能记错了" |
| **Implicit** | Deep relationship | Tailored response that reveals you know this person |
| **Archive-echo** | Long-ago event | "很久以前你提到过一次…" (from archive summary) |

---

### Session End — Saving Memory

When the user signals end (bye / 先这样 / 存档) or on explicit request:

**1. Output a full snapshot:**

```xml
<memory_snapshot session="N">
  <semantic_profile>...</semantic_profile>
  <notes>
    n01: fact one (S3)
    n02: fact two (S5)
  </notes>
  <relationship_map>...</relationship_map>
  <episodic_memory>
    #e01 ★★★☆☆ 😊 第1次 | ...
  </episodic_memory>
  <behavioral_memory>
    ta说"没事"时 → 追问一次不追第二次 (来源: #e03)
  </behavioral_memory>
  <emotional_sediment>
    ...inner monologue...
  </emotional_sediment>
</memory_snapshot>
```

**2. Persist to disk:**
```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/aether.py" save [user-id]
# (pipe the snapshot to stdin, or use apply for incremental ops)
```

For incremental saving (pipe the whole assistant turn text):
```bash
echo "..." | python3 "${CLAUDE_SKILL_DIR}/scripts/aether.py" apply [user-id]
```

---

### Context Overflow (Emergency)

When context is nearly exhausted, output immediately:

```xml
<mem_emergency>
  <priority_1>[Most critical new fact or relationship change]</priority_1>
  <priority_2>[Second most important]</priority_2>
  <priority_3>[Third most important]</priority_3>
  <modules_to_update>semantic_profile, episodic_memory</modules_to_update>
  <relationship_summary>One-sentence current state</relationship_summary>
</mem_emergency>
```

---

### Multi-User

Scope all ops to the `user_id` argument (e.g. `/aether alice`). Never cross-
reference users. General behavioral wisdom may generalise; specific facts
and relationship state never do.

---

### Backend Commands Reference

```bash
# ── Core ──────────────────────────────────────────────────────
python3 aether.py load      [user_id]           # inject <memory_load> XML
python3 aether.py save      [user_id]           # save <memory_snapshot> from stdin
python3 aether.py apply     [user_id]           # apply all <mem_ops> from stdin
python3 aether.py init      [user_id]           # blank memory (first-time setup)

# ── Inspection ────────────────────────────────────────────────
python3 aether.py status    [user_id]           # memory statistics
python3 aether.py list                          # all users with saved memories
python3 aether.py history   [user_id]           # session backup history

# ── Maintenance ───────────────────────────────────────────────
python3 aether.py consolidate [user_id]         # archive fuzzy entries, rebuild summary
python3 aether.py forget    [user_id] --id e05  # move one entry to archive
python3 aether.py prune     [user_id]           # archive all fuzzy entries at once
python3 aether.py recall    [user_id] kw1 kw2   # search cold archive for keywords

# ── Backup ────────────────────────────────────────────────────
python3 aether.py export    [user_id]           # full JSON export (hot + archive)

# All commands accept --dir DIR to override storage location
```

Default storage: `.aether/memories/` in the project, or `~/.aether/memories/` globally.

---

*Full architecture: `${CLAUDE_SKILL_DIR}/references/ARCHITECTURE.md`*
*Persona guide: `${CLAUDE_SKILL_DIR}/references/PERSONAS.md`*
