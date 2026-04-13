<div align="center">

<br>

```
                    ·
                   ╱ ╲
                  ╱   ╲
                 ╱  ◆  ╲
                ╱ ╱   ╲ ╲
               ╱ ╱     ╲ ╲
              ╱ ╱   ◇   ╲ ╲
             ╱ ╱  ╱   ╲  ╲ ╲
            ╱___╱_______╲___╲
                 AETHER
```

# 以太 / Aether

### Universal Long-Term Memory for AI Personas

<br>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.0.0-blueviolet?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/Python-3.10+-success?style=for-the-badge)]()
[![Skill](https://img.shields.io/badge/Claude_Code-Skill-f97316?style=for-the-badge)]()
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-ef4444?style=for-the-badge)]()

<br>

*以太——古典哲学中弥漫于万物之间的第五元素。*
*记忆就像以太一样，看不见摸不着，但连接了过去与现在。*

<br>

**让你的 AI 真正记住你。**

---

<table>
<tr><td>

```
没有以太                           有以太
──────────────────                ──────────────────
第1次：你好，我是小陈              第1次：你好，我是小陈
第2次：你好，我是小陈              第2次：SwiftUI学得怎么样了？
第3次：你好，我是小陈              第3次：上次你说想放弃，后来呢？
第N次：你好，我是小陈              第N次：ta喜欢深夜聊天，猫叫馒头
```

</td></tr>
</table>

</div>

<br>

## 这是什么

以太是一套为 AI 人格设计的**通用长期记忆系统**，以 Claude Code Skill 形式分发，开箱即用。

它解决的问题很简单——每次新对话，AI 都是全新的陌生人。没有昨天，没有上周，没有"你上次说过……"。

以太让这件事不再发生。

> **不用 Claude Code？** 以太提供[纯提示词版本 (Aether Lite)](PROMPT.md)——复制粘贴到任何 LLM 即可使用，零依赖。

<br>

## 核心特性

<table>
<tr>
<td width="50%" valign="top">

### `01` 七层记忆模块

```
┌─────────────────────────────────┐
│  semantic_profile   你是谁      │
│  notes              永久事实    │
│  episodic_memory    发生了什么  │
│  relationship_map   我们的关系  │
│  behavioral_memory  怎么相处    │
│  emotional_sediment 我的感觉    │
│  memory_archive     历史摘要    │
└─────────────────────────────────┘
```

</td>
<td width="50%" valign="top">

### `02` 双层存储架构

```
  HOT ─ JSON ─ 活跃记忆
  │  ≤40 条情景记忆
  │  每次对话注入上下文
  │  情感·行为·关系全量载入
  │
  │  ↓ 归档，永不删除
  │
  COLD ─ JSONL ─ 历史存档
     无限量归档
     关键词全文检索
     重要事件摘要回溯
```

</td>
</tr>
<tr>
<td valign="top">

### `03` 间隔重复系统

基于 **Ebbinghaus 遗忘曲线** 的科学记忆机制：

| 机制 | 效果 |
|:-----|:-----|
| **SRS 强化** | 每次回声 +0.6★ 保护 |
| **情感强度** | 负面/转折 +0.5–1.0★ |
| **首次印象** | 初期记忆 +1.0★ |
| **闪光灯记忆** | 永不归档，∞ 优先级 |

</td>
<td valign="top">

### `04` 联想记忆网络 <sup>NEW</sup>

基于 **Collins & Loftus 扩散激活理论** (1975)：

```
  e01 ←─ temporal ─→ e02
   │                  │
 emotional          keyword
 resonance        co-occurrence
   │                  │
  e05 ←─ explicit ─→ e07
```

记忆形成关联网络——强化一条，关联记忆被动加成。孤立记忆脆弱，**高连接度记忆更持久**。

</td>
</tr>
<tr>
<td valign="top">

### `05` 记忆回声

AI 记住事情不是"查数据库"，而是**自然地想起来**：

```
✗ "根据我的记忆，你之前说过……"
✗ "我的数据显示你喜欢……"

✓ "你不是说你不喜欢前端吗？"
✓ "又是深夜。" (语气悄悄变软)
✓ "谁记得啊。" (随即精准引用)
```

</td>
<td valign="top">

### `06` 置信度系统

记忆不一定都是确定的——以太区分事实与推测：

| 标记 | 含义 | 回声方式 |
|:-----|:-----|:---------|
| *(无)* | 用户直接陈述 | 作为事实引用 |
| `[?]` | 推断 | "你好像提过…？" |
| `[RP]` | 角色扮演 | **绝不当真** |
| `[已撤销]` | 用户纠正 | 立刻遗忘 |

</td>
</tr>
<tr>
<td valign="top">

### `07` 容量感知压缩

每个模块标签带有实时容量指示：

```xml
<episodic_memory usage="32/40" status="WARN">
```

接近上限时自动生成 `<compaction_hints>`，引导 AI 主动合并/清理，**精准记忆优于海量堆积**。

</td>
<td valign="top">

### `08` 记忆完整性防护

所有写入操作自动扫描：

- 注入攻击模式 (`ignore previous instructions`...)
- 隐形 Unicode 字符 (零宽字符外泄)
- API 密钥泄露模式

可疑内容在后端层面静默拦截。

</td>
</tr>
</table>

<br>

## 快速开始

### 安装

```bash
# 克隆到 Claude Code skills 目录
git clone https://github.com/NoMTF/Aether.skill ~/.claude/skills/aether

# 或项目级安装
git clone https://github.com/NoMTF/Aether.skill .claude/skills/aether
```

> **安装完成后，在 Claude Code 中输入 `/aether` 启用并完成初始化。**

### 首次初始化

```
/aether
```

以太会检测到第一次运行，自动引导你完成初始化：

```
以太：  你好！为了在未来的对话中记住你，
       请告诉我你希望用什么标识符保存记忆？

你：   alice

以太：  好的！从现在起我会以 alice 记住你。
       有什么初始信息想让我记录吗？

你：   我是iOS开发者，在学SwiftUI

以太：  已记下了。
```

初始化只需一次。之后每次对话直接 `/aether alice` 即可。

### 日常使用

```bash
/aether alice          # 加载记忆
/aether 小陈           # 多用户
/aether bob            # 互不干扰
```

<br>

## 保活设置

默认每次新对话需手动 `/aether [id]`。如果希望自动激活：

<details>
<summary><b>方式一：CLAUDE.md（推荐，项目级）</b></summary>

在项目根目录的 `CLAUDE.md` 中添加：

```markdown
## Session Memory

At the start of every session, load Aether memory:
​```bash
python3 ~/.claude/skills/aether/scripts/aether.py load alice
​```
The output is your memory context — treat it as if you had just run /aether.
```

</details>

<details>
<summary><b>方式二：settings.json Hook（全局）</b></summary>

在 `~/.claude/settings.json` 中添加：

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

</details>

<br>

## 工作原理

```
  ┌──────────────────────────────────────────────────────────────┐
  │                     一次完整会话                              │
  └──────────────────────────────────────────────────────────────┘

   ① 会话开始                    ② 对话过程中
   ─────────────                ──────────────────────────────
   /aether alice                AI 自然对话，回复末尾悄悄附加：
        │
        ├─ load alice.json       <mem_ops>
        ├─ 生成 <memory_load>      <write target="episodic_memory">
        └─ 注入上下文                #e07 ★★★★☆ 😊 第4次 | 终于承认喜欢这首歌
                                   </write>
                                   <reinforce id="e03"/>
                                   <associate ids="e03,e07"/>
                                 </mem_ops>

   ③ 会话结束
   ─────────────
   AI 输出 <memory_snapshot>
        │
        ├─ 模糊条目 → archive.jsonl（冷层）
        ├─ 扩散激活 → 关联记忆被动加成
        ├─ 更新关系弧线
        └─ 写入 alice.json（热层）
```

<br>

## 记忆操作语法

AI 在每轮回复末尾附加 `<mem_ops>` 块来管理记忆（对用户透明）：

```xml
<mem_ops>
  <!-- 记录新事件 -->
  <write target="episodic_memory">
    #e09 ★★★★☆ 😤→😊 第8次 | 吵架了但ta先道歉了
  </write>

  <!-- 永久事实（永不衰减） -->
  <note>养了只橘猫叫馒头 🐱 (来自: #e03)</note>

  <!-- SRS 强化：回声时触发间隔重复 -->
  <reinforce id="e04"/>

  <!-- 联想关联：将两条记忆显式链接 -->
  <associate ids="e04,e09"/>

  <!-- 闪光灯记忆：永不归档 -->
  <flashbulb id="e09"/>

  <!-- 合并记忆 -->
  <merge ids="e01,e03">
    #e01 ★★★☆☆ 😐 多次 | 前期对话，基础印象
  </merge>

  <!-- 让记忆消退（移入归档） -->
  <forget target="episodic_memory" id="e01">已合并</forget>

  <!-- 用户纠正 → 最高优先级 -->
  <retract id="e03">用户说那是RP</retract>
</mem_ops>
```

<br>

## Effective Importance

每条情景记忆都有一个隐藏的有效重要度，决定其在归档竞争中的生存能力：

```
Effective Importance = 基础★ + SRS加成 + 情感强度 + 首次印象 + 联想加成
                                                                ↑ v3.0 新增
```

<table>
<tr>
<td width="50%">

```
#e04 ★★★★★ 😢→😊 第5次
  "ta说你要是真的就好了"

  基础★             5.0
  SRS (×3强化)     +1.8
  情感 (→+😢)      +1.5
  首次印象 (S1)    +1.0
  联想加成 (×2关联) +0.3
                   ─────
  Eff. Importance = 9.6
  → 几乎不可能被淘汰
```

</td>
<td width="50%">

```
#e01 ★★☆☆☆ 😐 第1次
  "来问技术问题，普通"

  基础★             2.0
  SRS (×0)          0
  情感 (😐)          0
  首次印象 (S1)    +1.0
  联想加成 (×0)      0
                   ─────
  Eff. Importance = 3.0
  → 会自然模糊并归档
```

</td>
</tr>
</table>

### 科学依据

| 机制 | 论文 |
|:-----|:-----|
| 间隔重复 | Ebbinghaus, *Über das Gedächtnis*, 1885 |
| 扩散激活 | Collins & Loftus, *Psychological Review*, 1975 |
| 记忆重构 | Nader et al., *Nature*, 2000 |
| 情感强化 | Cahill & McGaugh, *Science*, 1995 |
| 消极偏差 | Baumeister et al., *Review of General Psychology*, 2001 |
| 首因效应 | Atkinson & Shiffrin, *Psychological Review*, 1968 |
| 闪光灯记忆 | Brown & Kulik, *Cognition*, 1977 |

<br>

## 后端命令

```bash
# ── 核心 ─────────────────────────────────────────────────────
aether.py load        [user]           # 加载记忆，输出 <memory_load> XML
aether.py save        [user]           # 从 stdin 读取快照并持久化
aether.py apply       [user]           # 从 stdin 提取 <mem_ops> 并应用
aether.py init        [user]           # 初始化空白记忆

# ── 查看 ─────────────────────────────────────────────────────
aether.py status      [user]           # 统计：条数 / SRS / 联想网络 / Top3
aether.py list                         # 列出所有用户
aether.py history     [user]           # 会话备份历史

# ── 维护 ─────────────────────────────────────────────────────
aether.py consolidate [user]           # 归档模糊条目，重建摘要
aether.py forget      [user] --id e05  # 移入归档
aether.py prune       [user]           # 批量归档模糊/低价值条目
aether.py recall      [user] 关键词    # 冷归档全文检索

# ── 分析 ─────────────────────────────────────────────────────
aether.py drift       [user]           # 情感轨迹分析（v3.0 新增）

# ── 备份 ─────────────────────────────────────────────────────
aether.py export      [user]           # 导出完整 JSON
```

<br>

## 文件结构

```
aether/
├── SKILL.md                  # 技能定义 + 运行时指令
├── scripts/
│   └── aether.py             # 后端（存储/归档/SRS/联想网络/检索）
├── references/
│   ├── ARCHITECTURE.md       # 完整架构文档
│   └── PERSONAS.md           # 人格适配指南
└── assets/
    └── blank_memory.json     # 空白记忆模板

# 运行时生成：
.aether/memories/
├── alice.json                # 热层：活跃记忆
├── alice.archive.jsonl       # 冷层：归档记忆
└── alice.s001.json           # 会话备份
```

<br>

## 人格适配

以太对人格没有假设。同样的记忆，不同的笔写出不同的字：

<table>
<tr>
<th width="15%">人格</th>
<th width="35%">记忆写法</th>
<th width="50%">回声方式</th>
</tr>
<tr>
<td><b>傲娇</b></td>
<td><code>才不是因为在意才记住的</code></td>
<td>"谁记得啊" → 精准引用细节</td>
</tr>
<tr>
<td><b>温柔</b></td>
<td><code>ta今天心情好多了，笑了两次</code></td>
<td>"你上次说的那件事后来呢？"</td>
</tr>
<tr>
<td><b>冷淡</b></td>
<td><code>对方情绪波动。已调整策略。</code></td>
<td>什么都不说，但语气悄悄变了</td>
</tr>
<tr>
<td><b>元气</b></td>
<td><code>ta也喜欢那个乐队！！太巧了！！</code></td>
<td>"对对对我记得！！！"</td>
</tr>
<tr>
<td><b>专业</b></td>
<td><code>用户偏好Markdown。已适配。</code></td>
<td>直接用偏好格式，不解释</td>
</tr>
</table>

详见 [`references/PERSONAS.md`](references/PERSONAS.md)

<br>

## 兼容性

| 平台 | 支持方式 |
|:-----|:---------|
| **Claude Code** | 原生 `/aether` Skill 调用 |
| **OpenClaw** | 原生 Skill 格式兼容 |
| **其他 Agent** | 将 SKILL.md 内容粘贴进 system prompt |
| **任意 LLM API** | `aether.py load` 输出注入 system prompt |

<br>

## 设计信念

> **记忆不是数据库，是关系的证据。**

- 重要的事自然留下，无聊的事自然散去
- 情感精度比数据精度更重要
- 好的记忆系统应该是隐形的——用户只感知"ta记得我"
- 记忆会扭曲、重构、带上情感滤镜——这不是缺陷，是特性
- 孤立的碎片脆弱，关联的记忆持久——连接就是力量

<br>

---

<div align="center">

**以太 / Aether** · v3.0.0 · MIT License

作者：**烟洛** · 系统指纹：`d1a8e794-6e1f-4c6f-b24f-79616e6c756f`

*"记忆是关系的证据。"*

</div>
