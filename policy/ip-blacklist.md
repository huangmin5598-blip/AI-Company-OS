# High Risk IP Blacklist (Novel-v1)

## S-Level Keywords (Trigger: ≥1 = HIGH RISK)
These keywords are highly indicative of known IP structures:

```
守夜人 | 神明代理 | 神选之人 | 神力继承 | 精神病院关押神
魔法学院 | 四大学院 | 分院制度 | 魔法考试
海军本部 | 忍者村 | 咒术高专 | 鬼杀队 | 猎魔人 | 特异局 | 调查兵团
```

**Rule**: Any 1 S-level keyword → HIGH RISK → REJECT

---

## A-Level Keywords (Trigger: ≥2 = HIGH RISK)
These indicate high template overlap:

```
系统提示 | 任务奖励 | 等级提升 | 属性面板
副本 | 任务世界 | 通关机制 | 轮回空间
宗门 | 内门弟子 | 外门弟子 | 长老 | 掌门 | 渡劫 | 飞升
末日组织 | 幸存者基地 | 资源争夺 | 变异体
能力评级 | 学院训练 | 天赋分级 | 异能觉醒
```

**Rule**: ≥2 A-level keywords → HIGH RISK → REVIEW

---

## Title Guard Patterns (Block Immediately)
These title structures are typical "shadow titles":

```
我在 + 地点/场所 + 学/当/成为 + 神/魔/仙/王/剑神/斩神
```

Examples:
- ❌ 《我在精神病院学斩神》
- ❌ 《我在守夜人当队长》
- ❌ 《我在魔法学院当学生》
- ❌ 《我当剑神那些年》

**Rule**: Match pattern → HIGH RISK → REJECT

---

## Safe Zone (Recommended)
These genres have minimal IP risk:

```
都市情感 | 婚恋关系 | 家庭冲突 | 身份反转 
职场故事 | 女性向爽文 | 豪门恩怨 | 契约婚姻 
先婚后爱 | 重生复仇（需差异化）
```

---

## Keyword Detection Logic

```
IF title matches "我在+地点+动词+神/魔/仙" pattern:
    → HIGH RISK → REJECT

IF any S-level keyword present:
    → HIGH RISK → REJECT

IF ≥2 A-level keywords present:
    → HIGH RISK → REVIEW

IF only B-level or safe zone:
    → LOW/MEDIUM RISK → PROCEED
```

---

## Plot Similarity Check (Heuristic)

**Question**: "Can a user explicitly name the novel this resembles?"

- **YES** (specific book name) → HIGH RISK → REJECT
- **NO** (only "like a genre") → SAFE → PROCEED

---

## Reference
- Full blacklist: `~/.openclaw/workspace/copyright-blacklist.md`
