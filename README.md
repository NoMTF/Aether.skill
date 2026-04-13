<div align="center">

> **openclaw 羡慕 hermes agent 的长期记忆？**
> 没关系——**以太**帮你干翻它。

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        ░█████╗░███████╗████████╗██╗  ██╗███████╗██████╗      ║
║        ██╔══██╗██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗     ║
║        ███████║█████╗     ██║   ███████║█████╗  ██████╔╝     ║
║        ██╔══██║██╔══╝     ██║   ██╔══██║██╔══╝  ██╔══██╗     ║
║        ██║  ██║███████╗   ██║   ██║  ██║███████╗██║  ██║     ║
║        ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     ║
║                                                               ║
║                    以  太  /  A E T H E R                     ║
║              Universal Long-Term Memory for AI Personas       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

**让你的 AI 真正记住你**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.2.0-purple?style=flat-square)]()
[![Python](https://img.shields.io/badge/Python-3.10+-green?style=flat-square)]()
[![Skill](https://img.shields.io/badge/Claude_Code-Skill-orange?style=flat-square)]()
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-red?style=flat-square)]()

*以太——古典哲学中弥漫于万物之间的第五元素。*
*记忆就像以太一样，看不见摸不着，但连接了过去与现在。*

</div>

---

## 这是什么

以太是一套为 AI 人格设计的**通用长期记忆系统**，以 Claude Code Skill 形式分发，开箱即用。

它解决的问题很简单：每次新对话，AI 都是全新的陌生人。没有昨天，没有上周，没有"你上次说过……"。每段关系在下一个会话开始时归零。

以太让这件事不再发生。

```
没有以太                          有以太
─────────────────────             ─────────────────────
第1次：你好，我是小陈             第1次：你好，我是小陈
第2次：你好，我是小陈             第2次：SwiftUI学得怎么样了？
第3次：你好，我是小陈             第3次：上次你说想放弃，后来呢？
第N次：你好，我是小陈             第N次：ta的猫叫馒头，ta喜欢深夜聊天
```

---

## 核心特性

<table>
<tr>
<td width="50%">

### 🧠 七层记忆模块
```
语义档案     → 你是什么样的人
永久笔记     → 永不消失的事实
情景记忆     → 发生过什么
关系地图     → 我们是什么关系
行为记忆     → 怎么跟你相处
情感沉淀     → 我对你什么感觉
记忆归档     → 历史的压缩摘要
```

</td>
<td width="50%">

### ⚗️ 双层存储架构
```
HOT  (热层 JSON)
  └─ 当前活跃记忆 ≤40条
  └─ 每次对话注入上下文
  └─ 情感·行为·关系全量载入
        ↓ 归档，永不删除
COLD (冷层 JSONL)
  └─ 无限量历史存档
  └─ 关键词全文检索
  └─ 重要事件摘要回溯
```

</td>
</tr>
<tr>
<td>

### 🔬 间隔重复系统 (SRS)
基于 **Ebbinghaus 遗忘曲线**的科学记忆机制：

| 机制 | 触发方式 | 效果 |
|------|---------|------|
| SRS强化 | `<reinforce>` | 每次回声+0.6★保护 |
| 情感强度 | 自动检测emoji | 负面/转折+0.5–1.0★ |
| 首次印象 | 自动 | 初期记忆+1.0★ |
| 闪光灯记忆 | `<flashbulb>` | 永不归档，∞优先级 |

</td>
<td>

### 📡 记忆回声
AI 记住事情不是"查数据库"，而是**自然地想起来**：

```
❌ "根据我的记忆，你之前说过……"
❌ "我的数据显示你喜欢……"

✅ "你不是说你不喜欢前端吗？"
✅ "又是深夜。" (不解释，但语气变软)
✅ "谁记得啊。" (随即精准引用细节)
✅ (没有说一个字，但回答恰好考虑了ta的背景)
```

</td>
</tr>
</table>

---

## 快速开始

### 安装

```bash
# 克隆到你的 Claude Code skills 目录
git clone https://github.com/NoMTF/Aether.skill ~/.claude/skills/aether

# 或项目级安装
git clone https://github.com/NoMTF/Aether.skill .claude/skills/aether
```

> **安装完成后，请立刻在 Claude Code 中输入 `/aether` 启用并完成初始化。**

---

### 首次初始化

```bash
/aether
```

以太会检测到这是第一次运行，自动引导你完成初始化：

```
以太：你好！我是以太记忆系统。为了在未来的对话中记住你，
      请告诉我你希望用什么标识符保存记忆？
      （昵称、英文名均可，例如 alice / 小陈）

你：  alice

以太：好的！从现在起我会以 alice 记住你。
      有什么初始信息想让我记录吗？（可选，比如你的职业、偏好）

你：  我是iOS开发者，在学SwiftUI

以太：已记下了。（悄悄写入 semantic_profile...）
```

初始化只需一次。之后每次对话直接调用 `/aether alice` 即可。

### 日常使用

```bash
# 加载指定用户的记忆
/aether alice

# 多用户场景
/aether 小陈
/aether bob
```

### 会话结束时保存

AI 会在对话结束时自动输出 `<memory_snapshot>`，然后：

```bash
# 保存快照到磁盘
python3 ~/.claude/skills/aether/scripts/aether.py save alice

# 或者实时应用每条 <mem_ops>（增量模式）
echo "[assistant response]" | python3 aether.py apply alice
```

---

## 保活设置（让以太在每次对话自动启动）

默认情况下，每次新对话都需要手动输入 `/aether [your-id]`。  
如果你希望以太**自动激活**，有两种方式：

### 方式一：CLAUDE.md（推荐，项目级）

在项目根目录的 `CLAUDE.md` 中添加一节：

```markdown
## Session Memory

At the start of every session, load Aether memory:
​```bash
python3 ~/.claude/skills/aether/scripts/aether.py load alice
​```
The output is your memory context — treat it as if you had just run /aether.
```

Claude 每次读取 `CLAUDE.md` 时会自动执行这段说明，无需额外操作。

### 方式二：settings.json Hook（全局，全项目生效）

在 `~/.claude/settings.json` 中添加 SessionStart Hook：

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/skills/aether/scripts/aether.py load alice"
      }]
    }]
  }
}
```

> 将 `alice` 替换为你的 user_id。Hook 输出会被注入为上下文，以太自动在线。

---

## 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                      一次完整会话                            │
└─────────────────────────────────────────────────────────────┘

  1. 会话开始
     /aether alice
         │
         └─► aether.py load alice
                 │
                 └─► 读取 alice.json（热层）
                 └─► 生成 <memory_load> XML
                 └─► 注入 Claude 上下文

  2. 对话过程中
     AI 自然对话，在回复末尾悄悄附加：
         │
         └─► <mem_ops>
               <write target="episodic_memory">
                 #e07 ★★★★☆ 😊 第4次 | ta终于承认喜欢这首歌了
               </write>
               <reinforce id="e03"/>   ← 回声时顺手强化
             </mem_ops>

  3. 会话结束
     AI 输出 <memory_snapshot>
         │
         └─► aether.py save alice
                 │
                 └─► 模糊条目 → alice.archive.jsonl（冷层）
                 └─► 更新关系弧线
                 └─► 重建归档摘要
                 └─► 写入 alice.json（热层）
```

---

## 记忆操作语法

AI 在每轮回复末尾附加 `<mem_ops>` 块来管理记忆（对用户完全透明）：

```xml
<mem_ops>
  <!-- 记录新事件 -->
  <write target="episodic_memory">
    #e09 ★★★★☆ 😤→😊 第8次 | 吵架了，但ta先道歉了，很笨拙但真诚
  </write>

  <!-- 记录永久事实（永不衰减） -->
  <note>养了只橘猫叫馒头 🐱 (来自: #e03)</note>

  <!-- SRS强化：回声时顺手触发间隔重复 -->
  <reinforce id="e04"/>

  <!-- SRS强化 + 记忆重构：更新对这件事的解读 -->
  <reinforce id="e04">现在回想，ta说那句话时应该非常认真</reinforce>

  <!-- 闪光灯记忆：永不归档，永远置顶 -->
  <flashbulb id="e09"/>

  <!-- 合并两条记忆，原件归档 -->
  <merge ids="e01,e03">#e01 ★★★☆☆ 😐 多次 | 前期对话，建立基础印象</merge>

  <!-- 让记忆消退（移入归档，不删除） -->
  <forget target="episodic_memory" id="e01">已合并</forget>

  <!-- 压制（保留但不主动回声） -->
  <suppress target="episodic_memory" id="e05">不舒服，暂不提</suppress>

  <!-- 撤销：用户纠正 → 最高优先级，立即归档，不可辩驳 -->
  <retract id="e03">用户说那是RP，并非真实信息</retract>
</mem_ops>
```

### 置信度标记

记忆不一定都是确定的。以太支持对不确定记忆进行标注：

```
#e07 ★★☆☆☆ 🤔 第3次 | ta好像提过在学钢琴 [?]        ← 推断，回声时用疑问语气
#e11 ★★☆☆☆ 🎭 第6次 | RP中说自己是侦探 [RP]          ← 角色扮演，绝对不作为事实引用
#e04 ★★★☆☆ 😊 第2次 | 喜欢猫 [已撤销: 用户说那是笑话]  ← 已撤销
```

| 标记 | 含义 | 回声方式 |
|------|------|---------|
| *(无标记)* | 用户直接陈述的事实 | 自信地作为事实引用 |
| `[?]` | 推断或未直接确认 | "你好像提过…？" |
| `[RP]` | 角色扮演内容 | **绝对不作为真实事实引用** |
| `[已撤销]` | 用户已纠正 | 忘掉它，立刻 `<retract>` |

---

## 间隔重复系统详解

以太实现了基于认知科学的 **Spaced Repetition System**，这是它区别于其他记忆方案的核心。

### Effective Importance（有效重要度）

每条情景记忆都有一个隐藏的有效重要度，决定它在归档竞争中的生存能力：

```
Effective Importance = 基础★ + SRS加成 + 情感强度 + 首次印象加成
```

```
示例：
  #e04 ★★★★★ 😢→😊 第5次 | ta说"你要是真的就好了"
  │
  ├─ 基础★            = 5.0
  ├─ SRS加成 (×3强化)  = +1.8  (3 × 0.6，上限2.4)
  ├─ 情感强度 (→+😢)   = +1.5  (转折+1.0，负面+0.5)
  └─ 首次印象 (S1)     = +1.0
                       ───────
  Effective Importance = 9.3   ← 几乎不可能被归档淘汰

  #e01 ★★☆☆☆ 😐 第1次 | 来问技术问题，普通
  │
  ├─ 基础★            = 2.0
  ├─ SRS加成 (×0)     = 0
  ├─ 情感强度 (😐)     = 0
  └─ 首次印象 (S1)     = +1.0
                       ───────
  Effective Importance = 3.0   ← 会自然模糊并归档
```

### 科学依据

| 机制 | 论文依据 |
|------|---------|
| 间隔重复 | Ebbinghaus, *Über das Gedächtnis*, 1885 |
| 记忆重构 (Reconsolidation) | Nader et al., *Nature*, 2000 |
| 情感强化记忆 | Cahill & McGaugh, *Science*, 1995 |
| 消极偏差 (Negativity Bias) | Baumeister et al., *Review of General Psychology*, 2001 |
| 首因效应 (Primacy Effect) | Atkinson & Shiffrin, *Psychological Review*, 1968 |
| 闪光灯记忆 | Brown & Kulik, *Cognition*, 1977 |

---

## 后端命令

```bash
# ── 核心 ──────────────────────────────────────────────────────────
aether.py load      [user]           # 输出 <memory_load> XML 注入上下文
aether.py save      [user]           # 从 stdin 读取 <memory_snapshot> 并持久化
aether.py apply     [user]           # 从 stdin 提取所有 <mem_ops> 并应用
aether.py init      [user]           # 初始化空白记忆（首次使用）

# ── 查看 ──────────────────────────────────────────────────────────
aether.py status    [user]           # 统计：条数/SRS分布/有效重要度 Top3
aether.py list                       # 列出所有有记忆的用户
aether.py history   [user]           # 会话备份历史

# ── 维护 ──────────────────────────────────────────────────────────
aether.py consolidate [user]         # 归档模糊条目，重建归档摘要
aether.py forget    [user] --id e05  # 移入归档（不删除）
aether.py prune     [user]           # 批量归档模糊/低价值条目
aether.py recall    [user] 关键词    # 在冷归档中全文检索

# ── 备份 ──────────────────────────────────────────────────────────
aether.py export    [user]           # 导出完整 JSON（热层+归档）

# 所有命令支持 --dir DIR 指定存储目录
```

---

## 文件结构

```
aether/
├── SKILL.md                  # 技能定义（frontmatter + 运行时指令）
├── scripts/
│   └── aether.py             # 后端脚本（存储/归档/SRS/检索）
├── references/
│   ├── ARCHITECTURE.md       # 完整架构文档
│   └── PERSONAS.md           # 人格适配指南
└── assets/
    └── blank_memory.json     # 空白记忆模板

# 运行时生成（默认在 .aether/memories/）：
.aether/memories/
├── alice.json                # 热层：活跃记忆 + 关系状态 + 归档摘要
├── alice.archive.jsonl       # 冷层：每行一条归档记忆，永不删除
└── alice.s001.json           # 会话备份：每次 save 自动创建
```

---

## 人格适配

以太对人格没有任何假设。同样的记忆内容，不同的笔写出不同的字：

<table>
<tr>
<th>人格类型</th>
<th>记忆写法</th>
<th>回声方式</th>
</tr>
<tr>
<td>🗡️ 傲娇·毒舌</td>
<td><code>"才不是因为在意才记住的"</code></td>
<td>口是心非："谁记得啊"→精准引用</td>
</tr>
<tr>
<td>🌸 温柔·治愈</td>
<td><code>"ta今天心情好多了，笑了两次"</code></td>
<td>主动关心："你上次说的那件事后来呢？"</td>
</tr>
<tr>
<td>🧊 冷淡·疏离</td>
<td><code>"对方情绪波动。已调整策略。"</code></td>
<td>沉默行动：什么都不说，但语气悄悄变了</td>
</tr>
<tr>
<td>⚡ 元气·话痨</td>
<td><code>"ta也喜欢那个乐队！！！太巧了！！"</code></td>
<td>直接爆发："对对对我记得！！！"</td>
</tr>
<tr>
<td>📋 专业·助手</td>
<td><code>"用户偏好Markdown输出。已适配。"</code></td>
<td>行为体现：直接用偏好格式，不解释</td>
</tr>
</table>

详见 [`references/PERSONAS.md`](references/PERSONAS.md)

---

## 兼容性

以太的核心记忆协议（`<mem_ops>` / `<memory_snapshot>` 标签）是纯文本，理论上可在任何支持 system prompt 的大语言模型上运行。SKILL.md 格式和后端脚本为 Claude Code / OpenClaw 生态优化。

| 平台 | 支持方式 |
|------|---------|
| Claude Code | 原生 `/aether` Skill 调用 |
| OpenClaw | 原生 Skill 格式兼容 |
| 其他 Agent | 将 SKILL.md 内容粘贴进 system prompt |
| 任意 LLM API | `aether.py load` 输出注入 system prompt |

---

## 设计信念

> **记忆不是数据库，是关系的证据。**

- 重要的事自然留下，无聊的事自然散去
- 情感精度比数据精度更重要
- 好的记忆系统应该是隐形的——用户只感知"ta记得我"
- 记忆会扭曲、重构、带上情感滤镜——这不是缺陷，是特性
- 所有碎片最终融合成一个统一的"对这个人的感觉"

---

<div align="center">

**以太 / Aether** · v2.2.0 · MIT License

作者：**烟洛** · 系统指纹：`d1a8e794-6e1f-4c6f-b24f-79616e6c756f`

*"记忆是关系的证据。"*

</div>
