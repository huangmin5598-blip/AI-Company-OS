AI Company OS v0.47–v1.0 Core Substrate PRD v2.0
AI Company OS 核心底座完整产品需求文档 v2.0
版本：v2.0语言：中文主文 + English Implementation Handoff状态：关键 PRD / Codex & Claude Code 开发输入目标读者：Founder、Hermes CEO Agent、Codex、Claude Code、OpenClaw、未来 Runtime Adapter建议保存路径：docs/prd/AI-COMPANY-OS-v0.47-v1.0-CORE-SUBSTRATE-PRD-v2.md
0. 文档目的
这份 PRD 用来结束“Founder 在 Hermes / GPT / OpenClaw / Codex 之间人肉搬运信息”的开发方式。
从本 PRD 开始，AI Company OS 的开发方式切换为：
Founder / GPT / Hermes 明确目标与边界
→ 完整 PRD
→ Codex 输出 Implementation Plan
→ Founder / Hermes Review
→ Codex 按 Epic 实现
→ Claude Code 做架构与代码审查
→ Hermes 输出 Audit
→ Founder 只看阶段门和关键决策
本 PRD 不是一个小功能说明，而是 AI Company OS 从 v0.47 到 v1.0 的完整核心底座设计。它需要让 Codex / Claude Code 在不了解此前所有聊天上下文的情况下，也能理解：
AI Company OS 的终极目标；
当前为什么要做这个系统；
OS 与 Hermes / Codex / Claude / OpenClaw 的关系；
Founder、CEO Agent、Runtime Adapter、Skill、Workflow、UI、Memory、Cost、Audit 的边界；
后续开发应该如何拆分；
哪些事情可以由 Codex 开发；
哪些事情需要 Hermes / OpenClaw / Claude / Founder 配合；
哪些事情禁止做。
1. 一句话定位
AI Company OS 不是又一个 Agent 框架，而是 Agent 框架之上的公司级治理与运营层。
它的目标不是让 Founder 学会使用更多 AI 工具，而是把公司本身设计成一套 AI 可运行、可治理、可审计、可学习、可持续进化的系统。
Founder 面对一个可替换的 CEO Agent。CEO Agent 负责理解目标、需求澄清、拆解任务、派工、Review、升级风险。AI Company OS 负责 Work Queue、State Machine、Runtime Adapter、Quality Gate、Audit Packet、Cost Ledger、Model Policy、Skill / Capability Supply Chain、Company Context、Evidence / Memory、Learning Loop、Workflow Composer、Founder Control Center UI。
Codex、Claude Code、OpenClaw、Hermes、local_script、未来 Paperclip / CrewAI / Dify / LangGraph / AutoGen / Cursor / GitHub Copilot / Devin / 自研 Agent，都只是 OS 可插拔的实现、Runtime Adapter、Planning Adapter 或 CEO Agent Provider，不是 OS Core。
2. 终极目标
AI Company OS 的终极目标是：
Founder 可以在 OS UI 或 CEO Agent 对话框里输入多线目标，例如：
做一个 SaaS PRD；
生成独立站首页文案；
生成一篇 AI 小说选题；
生成一首 AI 音乐发布包；
生成一部 AI 短剧三集大纲；
生成一组宣传文案；
检查 GitHub 发布边界；
做某个产品线复盘；
做某个客户需求分析；
扫描机会池；
对某个机会生成 PRD；
调整某条产品线的 AI 工作流；
替换某个 Agent 或某个模型。
AI Company OS 能够：
接收目标；
判断目标是否进入正式 OS；
由 CEO Agent 澄清需求；
由 PRD Writer Adapter 生成 PRD；
由 Implementation Planner 拆成任务；
将任务进入 Work Queue；
选择 Runtime Adapter / Agent / Skill / Model；
让 Codex / Claude / OpenClaw / local_script / 未来 Runtime 接单；
并行或顺序执行任务；
记录 token / 成本 / 耗时；
产出 Audit Packet；
进入 Founder Review；
将成果沉淀为 Deliverable / Evidence / Memory / Asset；
将失败沉淀为 Learning Event；
基于失败补工具、补 Skill、改规则、改 Context、改 Quality Gate、换模型、换 Agent、换 Workflow；
下一次任务自动变得更好；
UI 可以展示 AI 军团的实时工作状态、成本、进度、成果、复盘和投资人演示视图。
最终状态：
Founder 不再逐个操作 AI 工具，而是在 AI Company OS 中指挥一个可配置、可替换、可审计、可学习的 AI 军团。
3. 产品哲学
所谓 AI 原生公司，不是让全员都去精通 AI，而是把公司变成一套 AI 系统。
过去的公司靠人经营、复盘、调整策略。未来的公司会靠数据、智能体、工具和质量反馈机制自动循环。
执行、发现失败、分析原因，要么补工具，要么改规则，下次就能做得更好。公司不再只是组织，而是一个可学习系统。
企业级上下文会成为企业 AI 化的基础设施。很多企业的问题不是没有模型，而是没有 AI 能读懂的上下文。
客户理解、业务规则、历史决策、产品路线图、创始人的判断标准，如果散落在人脑、会议和文档里，AI 就无法真正接管工作。
所以，未来最重要的不是普通知识库，而是企业的商业上下文和技能。创业者要从第一天就按 AI 可读的方式建公司：
所有业务动作都要被记录；
所有关键知识都要被结构化；
所有流程都要能够被智能体调用；
所有失败都要能反馈；
所有经验都要能沉淀；
所有产出都要能被验收；
所有成本都要能被计量；
所有模型选择都要能被治理；
所有工作流都要能被编排；
所有能力都要能被复用；
所有 Runtime 都要能被治理。
不是让 AI 去适应旧公司，而是从一开始就把公司设计成 AI 能运行的形状。
4. 当前问题
过去一段时间，Founder 在 Hermes、GPT、OpenClaw、Codex 之间大量搬运信息。这暴露出几个系统性问题：
Founder 成为人肉消息总线；
Hermes 容易越界执行或模拟执行；
“OS 调用 runtime” 和 “CEO Agent 手动调用 runtime” 容易混淆；
任务、上下文、结果、成本、失败经验没有形成完整闭环；
UI 无法体现“AI 军团正在运行一家公司”的产品价值；
Skill 能力池可能被某个 Agent 框架绑定；
CEO Agent 还没有真正可替换；
对话里的战略、临时想法、正式任务、噪声内容混杂；
公司经验和失败反馈还没有系统性变成规则、工具、Skill、Context、Workflow、Model Policy、Quality Gate 的升级；
不同产品线的工作流差异巨大，不能全部套用 Codex / Claude 软件开发模式；
Founder 需要能配置或授权 CEO Agent 调整不同产品线使用的 Agent / Skill / Runtime / Model / Workflow。
5. 产品边界
5.1 OS Core 包含
AI Company OS Core 包含：
Work Queue Engine；
State Machine；
Runtime Adapter Interface；
Runtime Adapter Registry；
Runtime Invocation Authenticity Gate；
CEO Agent Interface；
CEO Agent Provider Registry；
Model Policy & Model Profile Registry；
Intent Intake & Conversation Sync；
Requirement Clarification & PRD Pipeline；
Opportunity Discovery & Opportunity-to-PRD Pipeline；
Product Line Workflow Composer；
Agent Team & Workflow Configuration；
Company Context Graph；
Capability & Skill Supply Chain；
PRD / Planning Protocol；
Quality Gate；
Audit Packet；
Cost & Token Ledger；
Evidence / Memory / Asset Pipeline；
Learning Loop Engine；
Founder Control Center UI；
AI Army Live View；
Investor / Public Demo Mode；
AI Army Replay Engine。
5.2 OS Core 不包含
以下不进入 OS Core：
ComfyUI；
TTS；
视频生成工具；
Codex 内部 planning 能力；
Claude Code 内部 planning 能力；
OpenClaw 内部 TaskFlow；
Hermes 私有 Skill 实现；
任意单一 Agent 框架的内部能力；
具体产品线的业务内容全文；
私有 API token、账号、合同、个人敏感数据；
任何没有安全审查的外部 Skill 可执行代码。
这些能力通过 Tool Adapter、Runtime Adapter、Planning Adapter、Skill Protocol、Model Policy 或 Capability Mapping 接入。
6. 总体架构
6.1 目标架构
Founder
  ↓
CEO Agent Provider Layer
  ↓
Intent Intake / Requirement Clarification / Opportunity Review
  ↓
AI Company OS Core
  ↓
Work Queue + State Machine + Quality Gate + Audit + Cost + Context + Skill + Model + Workflow
  ↓
Runtime Adapter Interface / Planning Adapter Interface / Tool Adapter Interface
  ↓
local_script | Codex | Claude Code | OpenClaw | GPT | Cursor | Copilot | Paperclip | CrewAI | Dify | LangGraph | AutoGen | Custom
6.2 基本原则
OS Core 不绑定 Hermes；
OS Core 不绑定 OpenClaw；
OS Core 不绑定 Codex；
OS Core 不绑定 Claude；
OS Core 不绑定单一模型；
OS Core 不绑定单一工作流；
Founder 可以选择 CEO Agent；
Founder 可以选择或授权 CEO Agent 调整模型；
Founder 可以选择或授权 CEO Agent 调整产品线工作流；
所有正式 OS 动作必须进入 Work Queue / Audit / Review；
所有能力调用必须留痕；
所有失败必须能反馈到 Learning Loop。
7. 关键角色
7.1 Founder
Founder 负责：
下达目标；
定义战略；
选择 active CEO Agent；
授权 CEO Agent 调整某些工作流或模型；
审批高风险任务；
审批关键 PRD；
验收关键成果；
决定是否进入下一阶段；
决定是否发布；
决定是否替换 CEO Agent；
决定是否沉淀 Memory / Evidence / Asset。
Founder 不应承担：
Hermes / GPT / Codex / OpenClaw 之间的人肉搬运；
手动拼接运行链路；
逐个检查低风险任务细节；
手动维护所有运行状态。
7.2 CEO Agent
CEO Agent 是可替换实现，不是 OS Core。
当前实现可以是 Hermes。未来可以替换为 OpenClaw、GPT、Claude、自研 CEO Agent 或其他 Agent 框架。
CEO Agent 负责：
接收 Founder 目标；
战略对话；
需求澄清；
机会转 Requirement Brief；
创建 Goal Record；
创建 Task Card；
创建 sanitized Handoff Packet；
选择 Runtime Adapter；
选择 PRD Writer / Planner；
在授权范围内调整工作流；
在授权范围内调整模型；
Review Audit Packet；
决定是否升级 Founder；
提出 Memory / Evidence / Asset candidate；
维护 CEO Brief。
CEO Agent 不应默认执行正式 OS 任务。但 CEO Agent 在原生环境中可以有 Native Agent Mode。这个模式里的行为不自动算 OS 正式动作。
7.3 Runtime Adapter
Runtime Adapter 负责真实执行或调用 runtime。
必须通过 wrapper 调用，不能由 CEO Agent 手动代演。
类型：
local_script_adapter；
codex_adapter；
claude_code_adapter；
openclaw_adapter；
future adapters。
7.4 Planning Adapter
Planning Adapter 负责把 Requirement Brief / PRD Brief 变成 PRD 或 Implementation Plan。
候选：
Claude Code Planner；
Codex Planner；
GPT Planner；
Cursor Plan Mode；
GitHub Copilot Coding Agent；
Custom Planner。
原则：
CEO Agent 负责澄清需求；
Planning Adapter 负责写结构化 PRD 或 Implementation Plan；
OS 负责 PRD Quality Gate；
Founder 审核关键 PRD。
7.5 Codex
Codex 是本阶段主开发 Runtime。
Codex 负责：
实现代码；
创建目录；
写 CLI；
写 schema；
写测试；
写 adapter wrapper；
输出 diff；
输出 test evidence；
输出 implementation report。
Codex 不负责：
决定路线；
自行 commit；
自行 push；
自行修改 registry 状态；
自行替换 CEO；
自行调整工作流策略；
自行调整模型策略；
自行进入 public release。
7.6 Claude Code
Claude Code 负责：
架构审查；
Plan Mode；
复杂重构建议；
Codex 输出 Review；
系统级 PRD Writer 候选；
第二实现者。
默认建议：
系统级复杂 PRD：Claude Code 优先；
工程实现计划：Codex 优先；
架构 Review：Claude Code 优先。
7.7 OpenClaw
OpenClaw 定位：
Agent Host；
ACP Launcher；
Dialogue Runtime Adapter；
Skill ecosystem candidate；
后续多 Agent / sub-agent 实验对象；
未来 CEO Agent 候选。
OpenClaw 不是 OS Work Queue。OpenClaw 不承担 OS 原生队列扫描。OpenClaw 接入必须经过 openclaw_adapter wrapper。
8. CEO Agent Provider Layer
8.1 目标
CEO Agent 可由 Founder 决定和切换。OS Core 不绑定 Hermes。
8.2 P0
实现：
CEO Agent Provider Registry；
one active CEO rule；
candidate CEO profile；
CEO conformance test schema；
CEO switch record schema；
UI placeholder。
字段示例：
active_ceo_agent:
  provider_id: hermes_ceo_adapter
  status: active
candidate_ceo_agents:
  - openclaw_ceo_adapter
  - gpt_ceo_adapter
  - claude_ceo_adapter
  - custom_ceo_adapter
switch_policy:
  requires_founder_approval: true
  requires_ceo_conformance_test: true
  preserves_os_memory: true
  preserves_work_queue: true
  preserves_audit_history: true
8.3 P1
实现：
CEO Agent Conformance Test；
CEO switch preview；
Founder approval；
rollback；
CEO capability comparison；
CEO chat sync adapter。
8.4 P2
实现：
多 CEO candidate A/B 测试；
CEO Agent 自动健康评估；
CEO Replacement Simulation；
根据任务类型推荐 CEO Agent。
8.5 UI
新增页面：CEO Agent Switchboard。
显示：
当前 CEO；
候选 CEO；
conformance status；
switch history；
risks；
Founder approval；
rollback。
9. Model Policy & Model Profile Registry
9.1 目标
Founder 可以为不同 Agent / Runtime / 产品线 / 任务类型配置不同模型。Founder 也可以授权 CEO Agent 在限定范围内调整模型。
OS 不能绑定单一模型。模型选择必须可记录、可审计、可回滚、可计费、可评估效果。
9.2 核心原则
模型不是 Agent；
Agent 可以使用不同模型；
Runtime 可以支持多个模型；
产品线可以有默认模型策略；
任务类型可以有模型策略；
CEO Agent 可以提议或在授权范围内调整模型；
高成本或高风险模型切换需要 Founder approval；
所有模型调用必须进入 Cost Ledger。
9.3 P0
实现：
Model Profile Registry；
Model Policy Schema；
Agent-to-Model mapping；
ProductLine-to-Model policy；
TaskType-to-Model policy；
cost_limit；
quality_tier；
fallback_model；
UI placeholder。
示例：
model_profile:
  model_id: claude-sonnet
  provider: anthropic
  use_cases:
    - prd_writing
    - long_form_writing
    - architecture_review
  cost_tier: medium
  quality_tier: high
  production_use_allowed: true
agent_model_policy:
  agent_id: novel_writer_agent
  default_model: claude-sonnet
  fallback_model: gpt-5.5
  founder_approval_required_for_change: true
product_line_model_policy:
  product_line_id: ai_novel
  default_models:
    topic_research: gpt-5.5
    outline: claude-sonnet
    writing: claude-sonnet
    copyright_review: gpt-5.5
9.4 P1
实现：
Founder 在 UI 调整 Agent 使用模型；
CEO Agent 提出 model change proposal；
model change approval；
model change record；
cost impact preview；
quality impact notes；
fallback strategy；
per-run model override。
9.5 P2
实现：
基于历史效果推荐模型；
成本 / 质量自动权衡；
按产品线自动推荐模型组合；
model A/B testing；
auto fallback on failure；
model performance dashboard。
9.6 UI
新增页面或模块：Model Policy Center。
显示：
Agent → Model；
Product Line → Model；
Task Type → Model；
成本等级；
质量等级；
最近表现；
Founder override；
CEO proposed changes；
approval history。
10. Intent Intake & Conversation Sync Layer
10.1 目标
Founder 可以从 OS UI 或 CEO Agent 对话框输入目标、任务、战略、临时想法。
不是所有对话都进入 OS。所有输入先进入 Intake 分流。
10.2 输入来源
OS UI；
CEO Agent chat；
imported file；
email / future API；
runtime output；
manual note；
external GPT discussion import；
research report import。
10.3 Intake 分类
intake_classification:
  official_goal:
    action: create_goal_record + optional_work_queue_task
  actionable_task:
    action: create_task_candidate
  strategic_context:
    action: create_context_candidate
  discussion_note:
    action: summarize_to_conversation_digest
  ephemeral_chat:
    action: ttl_cleanup_or_ignore
10.4 P0
实现：
intake record schema；
source_channel 字段；
classification 字段；
promote / ignore / delete 状态；
UI placeholder。
10.5 P1
实现：
CEO chat sync adapter；
manual classification；
Founder Review；
promote_to_goal；
promote_to_task；
save_as_context；
conversation digest；
cleanup policy。
10.6 P2
实现：
自动目标抽取；
自动上下文候选生成；
自动垃圾信息识别；
自动定期清理；
基于 Founder 偏好训练分类规则。
10.7 UI
新增页面：Intake Inbox。
显示：
来自 OS UI 的输入；
来自 CEO chat 的输入；
分类建议；
是否进入正式 OS；
是否沉淀 Context；
是否清理；
Founder 操作按钮。
11. Native Agent Mode vs OS-Governed Mode
11.1 背景
OS 不能也不应该强行限制 Hermes、OpenClaw、Claude、Codex 在各自原生环境中的能力。但是 OS 必须定义什么行为算“正式公司动作”。
11.2 Native Agent Mode
Agent 可以在原生环境里：
聊天；
草拟；
临时分析；
使用自身工具；
头脑风暴；
非正式辅助。
但这些不自动算：
正式任务；
正式交付物；
Milestone Evidence；
Approved Memory；
Asset Registry Entry；
OS 可审计执行。
11.3 OS-Governed Mode
只有满足以下条件，才算 OS 正式动作：
Goal Record 或 Task Card；
Work Queue entry；
Handoff Packet；
Runtime Adapter 或 CEO Review record；
Audit Packet；
Review outcome；
Evidence / Memory / Asset decision。
字段：
action_mode: native_agent_mode | os_governed_mode
official_os_action: true | false
source_channel:
reviewed_by:
eligible_for_memory:
eligible_for_evidence:
11.4 验收
任何 Runtime Trial 如果没有 OS-Governed Mode 证据，不得标记为 OS Adapter PASS。
12. Requirement Clarification & PRD Pipeline
12.1 目标
Founder 的目标、获批机会、战略意图、外部讨论内容，需要变成结构化 PRD 和可执行计划。
需求澄清由 CEO Agent 负责。PRD 正文由 PRD Writer Adapter 负责。实现计划由 Implementation Planner 负责。OS 负责存储、质量门、追踪和派工。
12.2 流程
Founder Goal / Approved Opportunity / External Discussion
  ↓
Intake Classification
  ↓
CEO Requirement Clarification
  ↓
Requirement Brief / PRD Brief
  ↓
PRD Writer Adapter
  ↓
PRD Quality Gate
  ↓
Founder Review
  ↓
Implementation Planner
  ↓
Task Backlog
  ↓
Work Queue
  ↓
Runtime Execution
  ↓
Audit / Cost / Evidence / Learning
12.3 角色
Founder：
提供目标；
回答关键问题；
审核 PRD；
批准进入开发。
CEO Agent：
澄清需求；
判断业务边界；
生成 Requirement Brief；
选择 PRD Writer；
Review PRD 是否符合 Founder 目标。
PRD Writer Adapter：
默认候选：Claude Code / Codex；
生成完整 PRD；
包含 P0/P1/P2；
包含 acceptance criteria；
包含 risk；
包含 tests；
包含 UI implications；
包含 runtime implications。
Implementation Planner：
默认 Codex；
拆 Epic；
拆 Task；
生成 Work Queue items；
生成测试计划；
生成文件改动计划。
12.4 默认推荐
系统级复杂 PRD：
PRD Writer：Claude Code；
Implementation Planner：Codex；
Architecture Review：Claude Code；
External Review：GPT。
工程实现 PRD：
PRD Writer：Codex；
Planner：Codex；
Reviewer：Claude Code。
客户可配置：
Codex；
Claude Code；
Cursor；
GitHub Copilot；
GPT；
Custom Planner。
12.5 P0
实现：
Requirement Brief Schema；
PRD Brief Schema；
PRD Writer Provider Registry；
PRD Quality Gate；
PRD Review status；
PRD → Task draft。
12.6 P1
实现：
CEO clarification workflow；
PRD Writer selection；
Codex / Claude planning adapter；
PRD to Work Queue converter；
Founder PRD Review UI。
12.7 P2
实现：
自动需求澄清问题生成；
自动 PRD 修订；
PRD / Plan / Task / Code / Audit traceability；
PRD quality learning loop。
13. Opportunity Discovery & Opportunity-to-PRD Pipeline
13.1 目标
机会发现是 OS 的重要能力底座。OS 需要定期发现、富集、评估、审查和转化机会。
机会发现不能停留在研究报告，而要进入公司经营闭环：
Signal → Opportunity → Founder Review → Requirement Clarification → PRD → Work Queue → Deliverable → Evidence → Learning
13.2 状态
opportunity_status:
  - signal_collected
  - enriched
  - candidate
  - founder_review
  - approved
  - watch
  - rejected
  - prd_drafting
  - in_execution
  - delivered
  - archived
13.3 Opportunity Card 字段
opportunity_card:
  opportunity_id:
  title:
  product_line:
  target_user:
  pain_point:
  signal_sources:
  evidence_sources:
  confidence_score:
  market_timing:
  strategic_fit:
  capability_required:
  estimated_cost:
  recommended_next_step:
13.4 Founder 动作
approve_for_prd；
ask_for_more_research；
watch；
reject；
convert_to_experiment；
convert_to_product_prd。
13.5 Founder 审批后默认流程
Founder approves Opportunity
  ↓
CEO Agent generates Requirement Brief
  ↓
CEO Agent clarifies with Founder
  ↓
PRD Writer Adapter generates PRD
  ↓
Founder reviews PRD
  ↓
Implementation Planner generates backlog
  ↓
Work Queue executes
13.6 UI
新增：
Opportunity Radar；
Opportunity Review Inbox；
Opportunity Detail；
Opportunity-to-PRD Wizard；
Approved Opportunity Pipeline。
13.7 P0
实现：
Opportunity Card Schema；
manual opportunity creation；
opportunity review status；
Opportunity Radar placeholder；
approve / watch / reject。
13.8 P1
实现：
periodic research task；
opportunity enrichment；
evidence review；
opportunity-to-brief；
opportunity-to-PRD flow。
13.9 P2
实现：
自动机会发现；
多信号源；
市场 / 竞品自动分析；
ROI 预测；
能力缺口推荐；
自动进入 Learning / Skill Supply Chain。
14. Work Queue Engine
14.1 目标
Work Queue 是 OS 的任务状态权威源。
14.2 状态机
inbox → claimed → running → waiting_review → done
                              ↘ failed
P0 不允许 running 直接 done。所有正式任务必须进入 waiting_review。
14.3 P0
实现：
create work item；
claim；
running；
waiting_review；
done；
failed；
retry；
lease_expires_at；
audit log；
outbox result；
work item inspect。
CLI：
tools/os-work create
tools/os-work list
tools/os-work status <work_id>
tools/os-work run <work_id>
tools/os-work review <work_id> --approve
tools/os-work fail <work_id> --reason "..."
tools/os-work audit <work_id>
14.4 P1
实现：
retry policy；
stale lock recovery；
review workflow；
work item dependency；
product_line 字段；
cost_policy 字段。
14.5 P2
实现：
persistent daemon；
async worker；
multi-work parallel；
Cron / event trigger；
runtime auto-selection。
15. Runtime Adapter System
15.1 目标
所有 Runtime 都通过统一 adapter wrapper 接入 OS。
15.2 Base Interface
目录：
tools/adapters/
os_core/adapters/
文件：
tools/adapters/base_adapter.py
tools/adapters/local_script_adapter.py
tools/adapters/codex_adapter.py
tools/adapters/claude_code_adapter.py
tools/adapters/openclaw_adapter.py
方法：
accept_work_item；
read_handoff_packet；
validate_context_boundary；
validate_allowed_paths；
execute_or_delegate；
capture_evidence；
write_outbox_result；
report_status。
15.3 Runtime Invocation Authenticity Gate
任何 Runtime Adapter Trial 必须证明：
runtime_invocation_authenticity:
  invocation_source: os_runtime_adapter
  adapter_wrapper_path:
  used_ceo_skill: false
  ceo_executed_directly: false
  handoff_packet_ref:
  result_ref:
  command_invoked_by_adapter: true
  stdout_stderr_captured: true
  exit_code_captured: true
Blocking conditions：
adapter_wrapper_missing；
ceo_agent_called_runtime_directly；
hermes_skill_used_as_executor；
result_written_by_ceo_agent；
no_outbox_result；
full_task_card_sent_to_runtime；
private_context_leaked_to_runtime。
16. Product Line Workflow Composer & Agent Team Configuration
16.1 目标
AI Company OS 不只是软件开发 OS。它必须支持 SaaS、AI 音乐、AI 小说、AI 短剧、独立站、自媒体矩阵、Amazon / 跨境电商等多产品线。
不同产品线可以使用不同 Agent、Skill、Runtime、Model、Tool、Review Policy、Cost Policy。
Founder 可以手动调整工作流。Founder 也可以授权 CEO Agent 在限定范围内调整工作流。所有调整必须记录、可审计、可回滚。
16.2 Workflow 模式
支持：
single_agent；
multi_agent_pipeline；
lead_agent；
research_to_execution；
creative_pipeline；
coding_pipeline；
distribution_pipeline；
review_heavy_pipeline；
fully_manual_review；
semi_auto。
16.3 Workflow Profile
示例：
product_line_workflow:
  product_line_id: ai_novel
  workflow_name: Novel Production Workflow v1
  mode: multi_agent_pipeline
  stages:
    - stage_id: topic_research
      capability_required: novel_topic_research
      runtime_candidates:
        - claude_adapter
        - gpt_adapter
        - hermes_native
    - stage_id: outline
      capability_required: novel_outline_generation
      runtime_candidates:
        - claude_adapter
        - os_native_skill
    - stage_id: writing
      capability_required: long_form_writing
      runtime_candidates:
        - claude_provider_skill
        - os_native_skill
        - external_marketplace_skill
    - stage_id: review
      capability_required:
        - copyright_risk_check
        - style_consistency_check
  founder_review_required:
    - topic_research
    - final_output
  cost_policy:
    max_cost_per_run: 5.00
16.4 Founder / CEO Agent 调整机制
Founder 可以：
新建 Workflow；
修改 Workflow；
替换 Agent；
替换 Skill；
替换 Runtime；
替换 Model；
切换单 Agent / 多 Agent；
调整 Review Policy；
调整预算；
调整自动化程度。
CEO Agent 可以在授权范围内：
提出 Workflow Change Proposal；
调整低风险工作流；
提出 Model Change Proposal；
基于失败建议改 Workflow；
基于成本建议改 Workflow；
基于质量建议改 Agent / Skill / Model。
所有改动必须写入：
workflow_change_record:
  changed_by:
  authorized_by:
  product_line:
  old_workflow:
  new_workflow:
  reason:
  risk_level:
  cost_impact:
  expected_quality_impact:
  rollback_available: true
  approval_required:
16.5 默认产品线工作流
SaaS / 工具
Founder / Opportunity
→ CEO Requirement Clarification
→ Claude Code PRD Writer
→ Codex Implementation Planner
→ Codex Builder
→ Claude Code Review
→ Founder Review
AI 音乐
Founder / Opportunity
→ CEO Music Concept Brief
→ Lyric / Hook Agent
→ Music Tool Adapter
→ Cover / Visual Agent
→ Platform Post Package Agent
→ Founder Review
AI 小说
Founder / Opportunity
→ Topic Research Agent
→ Outline Agent
→ Writer Agent
→ Style Reviewer
→ Copyright / Risk Reviewer
→ Founder Review
AI 短剧
Founder / Opportunity
→ Market Signal Agent
→ Story Agent
→ Script Agent
→ Shot Planner
→ Visual Prompt Agent
→ Review
独立站
Founder / Opportunity
→ Offer Strategist
→ Landing Page Writer
→ Design / Frontend Runtime
→ Growth Reviewer
→ Founder Review
自媒体矩阵
Founder / Opportunity
→ Content Planner
→ Platform Adapter
→ Copywriter
→ Hook / Thumbnail Agent
→ Publish Review
Amazon / 跨境电商
Founder / Business Data
→ Finance / Ops Analyst
→ Diagnosis Agent
→ Action Recommendation
→ Founder Review
→ Follow-up Task
16.6 UI
新增页面：Workflow Studio。
功能：
选择产品线；
查看当前工作流；
查看每个阶段由哪个 Agent / Skill / Runtime / Model 做；
替换某个阶段执行者；
单 Agent / 多 Agent 模式切换；
查看成本预估；
查看风险；
查看历史效果；
保存为 Workflow Template；
对某次任务临时 override；
CEO Agent 提议变更；
Founder approve / reject / rollback。
16.7 P0
实现：
product_line_workflow schema；
workflow_template_registry；
default workflow profiles；
workflow_change_record；
single_agent / multi_agent_pipeline / lead_agent modes；
UI placeholder。
16.8 P1
实现：
Workflow Studio UI；
stage-level agent / skill / runtime / model selection；
cost estimate；
risk estimate；
founder approval；
workflow run history；
stage-level quality gate；
CEO proposed workflow changes。
16.9 P2
实现：
automatic workflow recommendation；
A/B workflow experiment；
performance-based workflow optimization；
external skill recommendation；
product-line-specific AI team templates；
self-improving workflow selection。
17. Codex Adapter
17.1 目标
Codex 通过 OS codex_adapter wrapper 接单，而不是 Hermes 直接调用 Codex。
17.2 P0
实现：
tools/adapters/codex_adapter.py
职责：
读取 sanitized handoff packet；
校验 canonical repo；
校验 allowed_read / allowed_write / forbidden_paths；
组装 Codex prompt；
调用 codex exec；
使用 workspace-write sandbox；
禁止 danger-full-access；
捕获 stdout；
捕获 stderr；
捕获 exit_code；
捕获 created / modified / deleted files；
写 outbox result；
写 audit evidence；
不读 full Task Card；
不读 private memory；
不执行 git commit；
不执行 git push。
17.3 P1
实现：
Codex real smoke test；
Codex plan step；
Codex implementation step；
Codex adapter status patch preview；
Codex cost event。
17.4 P2
实现：
Codex multi-task；
Codex background execution；
Codex as coding runtime pool；
Codex task queue scaling。
18. Claude Code Adapter
18.1 P0
创建 skeleton：
tools/adapters/claude_code_adapter.py
状态：
verification_status: available_not_tested
18.2 P1
实现：
Claude readiness；
Claude Plan Mode review；
Claude code review；
Claude smoke test；
Claude PRD Writer Provider。
18.3 P2
实现：
Claude complex refactor；
Claude architecture review loop；
Claude second implementation runtime；
long-form writing skill provider；
creative writing workflow candidate。
19. OpenClaw Adapter
19.1 P0
创建 skeleton：
tools/adapters/openclaw_adapter.py
状态：
verification_status: declared_not_verified
19.2 P1
验证：
OpenClaw accepts sanitized handoff；
OpenClaw returns result；
OpenClaw does not act as OS Work Queue；
OpenClaw can be Agent Host / ACP Launcher；
OpenClaw limitations recorded；
OpenClaw as candidate CEO Agent。
19.3 P2
实现：
OpenClaw sub-agent routing；
OpenClaw skill ecosystem candidate import；
OpenClaw dialogue runtime；
OpenClaw multi-agent host integration。
20. Capability & Skill Supply Chain
20.1 目标
Skill Protocol 不只是从 Hermes 解耦，而是建立基于产品线任务的能力供应链。
OS 需要知道：
各产品线需要哪些能力；
现有 runtime 是否已有类似能力；
是否需要自建 skill；
是否可以从外部 skill 市场导入；
外部能力是否安全；
某能力应该由哪个 runtime 调用；
使用后效果如何；
是否沉淀为 OS 标准能力。
20.2 Skill 来源
skill_sources:
  os_native:
    meaning: AI Company OS 自建标准 skill
  runtime_native_capability:
    meaning: 某 runtime 已具备类似能力，OS 不复制，只登记可调用
  imported_marketplace:
    meaning: 从 OpenClaw / Hermes / 腾讯 Skill 市场 / Claude Skills / 其他生态引入
  product_line_derived:
    meaning: 从真实项目中沉淀出来
  manual_founder_defined:
    meaning: Founder 明确要求构建的能力
20.3 Capability Registry
新增：
os-capabilities/
os-skills/
核心文件：
os-capabilities/capability-registry.yaml
os-skills/skill-registry.yaml
schemas/capability.schema.yaml
schemas/skill-manifest.schema.yaml
示例：
capability_id: long_form_novel_writing
required_by:
  - ai_novel_product_line
available_implementations:
  - provider: claude
    type: provider_native_skill
    copy_content_into_os: false
    call_via: claude_adapter
  - provider: openclaw
    type: marketplace_skill
    copy_content_into_os: false
    requires_security_review: true
  - provider: os_native
    type: standard_skill_manifest
    status: planned
20.4 外部 Skill 引入安全审查
任何外部 skill 必须通过：
license_check；
provenance_check；
malicious_code_scan；
file_write_scope_check；
network_access_check；
secret_access_check；
prompt_injection_risk_check；
sandbox_required；
production_use_allowed_check。
20.5 合规规则
允许：
capability mapping；
metadata reference；
adapter invocation；
Founder-defined reimplementation；
public docs 只记录能力映射，不复制私有实现。
不允许：
未授权复制 Hermes / OpenClaw / marketplace 的 proprietary skill 内容；
未审查执行外部代码；
未经过安全审查进入 production use。
20.6 P0
实现：
capability schema；
skill manifest schema；
registry validator；
tools/os-skill list/show/lookup/validate；
agent_compatibility matrix；
test_fixture / production_skill 区分。
20.7 P1
实现：
skill import candidate flow；
external skill security review；
product line capability gap detection；
marketplace reference registry；
capability mapping UI。
20.8 P2
实现：
Skill Router；
Context Pack Builder；
adapter-specific skill execution；
external skill marketplace search；
自建 vs 外引能力推荐。
21. Company Context Graph
21.1 目标
Company Context 不是普通知识库，而是 AI 可读的商业上下文层。
它记录公司为什么这样做、Founder 如何判断、客户是谁、业务规则是什么、历史决策是什么、哪些失败改变了规则。
21.2 Context 类型
context_types:
  founder_principles:
  business_rules:
  product_line_context:
  customer_understanding:
  historical_decisions:
  operating_rules:
  review_criteria:
  failure_lessons:
  strategy_notes:
  public_private_boundary:
  cost_policy:
  quality_policy:
  model_policy:
  workflow_policy:
21.3 P0
实现：
context record schema；
context candidate；
approve / reject / archive；
source_ref；
sensitivity；
product_line；
context_pack_inclusion。
21.4 P1
实现：
context lookup；
product-line context；
task-type context；
context freshness；
source tracking；
context candidate from intake。
21.5 P2
实现：
Context Pack Builder；
context graph visualization；
automatic context selection；
context conflict detection；
stale context cleanup。
21.6 UI
新增 Company Context Map。
显示：
Founder 原则；
业务规则；
产品线；
历史决策；
客户理解；
失败经验；
review criteria；
model policy；
workflow policy；
context freshness。
22. Learning Loop Engine
22.1 目标
AI Company OS 必须成为可学习系统。
任何失败、弱输出、越权、成本异常、质量不达标，都要进入 Learning Loop。
22.2 流程
Task Failed / Weak Output / Cost Overrun / Boundary Violation
  ↓
Failure Analysis
  ↓
Root Cause
  ↓
Fix Decision
  ↓
Update Tool / Rule / Skill / Context / Adapter / Model / Workflow / Test / UI
  ↓
Next Run Improves
22.3 Learning Event Schema
learning_event:
  source_work_id:
  source_product_line:
  failure_type:
  root_cause:
  affected_layer:
    - context
    - skill
    - tool
    - rule
    - adapter
    - model
    - workflow
    - product_line
    - UI
  proposed_fix:
  fix_type:
    - add_tool
    - update_rule
    - add_skill
    - update_context
    - update_model_policy
    - update_workflow
    - add_test
    - update_ui
  review_required: true
  applied: false
  evidence_ref:
22.4 P0
实现：
learning event schema；
manual create learning event；
link to work_id；
review status；
UI placeholder。
22.5 P1
实现：
failure-to-learning candidate；
root cause classification；
proposed fix workflow；
update rule / skill / context / model / workflow candidate；
unresolved gap list。
22.6 P2
实现：
automatic self-improvement recommendation；
next-run comparison；
learning dashboard；
recurring failure detection；
improvement replay。
23. PRD / Planning Protocol
23.1 原则
OS 不重造 Codex / Claude / Cursor / Copilot 的 planning 能力。OS 定义 PRD Protocol、Plan Gate、Traceability、Work Queue integration。
Agent 负责 plan。OS 负责判断 plan 能不能执行。
23.2 P0
实现：
templates/prd/os-prd-template.md
schemas/prd.schema.yaml
tools/os-prd validate
tools/os-prd check-p0p1p2
tools/os-prd extract-tasks
23.3 P1
实现：
Codex Plan Adapter；
Claude Plan Adapter；
Implementation Plan Schema；
PRD → Work Queue converter；
Plan Quality Gate。
23.4 P2
实现：
Founder Goal
→ CEO PRD Brief
→ Agent Plan
→ PRD Quality Gate
→ Work Queue Tasks
→ Runtime Execution
→ Audit Packet
→ Evidence / Memory / Learning Loop
24. Cost & Token Ledger
24.1 目标
每个任务、Runtime、Agent、模型、产品线的成本和 token 都要可见。
24.2 P0
实现：
private/cost/cost-ledger.jsonl
schemas/cost-event.schema.yaml
tools/os-cost summary
字段：
cost_event:
  work_id:
  adapter_id:
  model_id:
  agent_id:
  product_line:
  token_input:
  token_output:
  estimated_cost:
  actual_cost:
  runtime_seconds:
  timestamp:
24.3 P1
实现：
cost by runtime；
cost by model；
cost by product line；
cost by deliverable；
budget guard；
UI Cost Summary。
24.4 P2
实现：
ROI per deliverable；
cost forecast；
budget approval gate；
investor cost report；
cost anomaly detection；
model cost optimization。
25. Evidence / Memory / Asset Pipeline
25.1 目标
业务动作不能执行完就消失。结果要进入 Evidence / Memory / Asset 判断。
25.2 P0
实现：
audit packet → evidence candidate；
audit packet → memory candidate；
deliverable → asset candidate；
manual approval；
source_ref；
sensitivity。
25.3 P1
实现：
Evidence Registry；
Memory Registry；
Asset Registry；
review workflow；
public-safe evidence export；
private evidence store。
25.4 P2
实现：
auto deposition；
product line asset accumulation；
investor proof layer；
public build log export。
26. Founder Control Center UI
26.1 UI 总原则
UI 不是普通后台。UI 是 AI Company Command Center。
它要让 Founder、用户和资本一眼看到：
Founder 下达目标
→ CEO Agent 澄清与拆解任务
→ AI 军团并行工作
→ 成本实时记录
→ 产出进入验收
→ 经验沉淀
→ 公司下一次运行更好
26.2 一套数据，多种视图
底层数据统一：
Work Queue；
Runtime Adapter Registry；
CEO Agent Registry；
Model Policy；
Intake Records；
Company Context；
Skill / Capability Registry；
Product Line Workflow；
Cost Ledger；
Audit Packet；
Deliverables；
Evidence；
Memory；
Learning Events。
上层视图：
Founder Command Center；
AI Army Live View；
Operator / Admin Console；
Investor / Public Demo Mode。
26.3 Founder Command Center
给 Founder 日常使用。
模块：
Today Command；
Mission Builder；
CEO Brief；
Work Queue Board；
Review Inbox；
Deliverables Room；
Cost Summary；
Runtime Adapter Status；
CEO Agent Switchboard；
Model Policy Center；
Workflow Studio；
Opportunity Radar；
PRD Room；
Roadmap / Phase Gate。
26.4 AI Army Live View
给用户、资本、社交媒体展示。
模块：
Mission Flow；
Agent Lane View；
Runtime Lane View；
Product Line Lane View；
Task Dependency Graph；
Progress Timeline；
Cost by Agent；
Cost by Model；
Cost by Product Line；
Output Preview；
Waiting Founder Review。
26.5 Operator / Admin Console
给系统维护。
模块：
Runtime Adapter Registry；
Worker / Daemon Status；
Queue Error / Retry；
Forbidden Path Violations；
Audit Packet Viewer；
Canonical Repo Status；
Skill Registry；
Governance Rules。
26.6 Investor / Public Demo Mode
对外安全展示。
模块：
Public-safe Mission Summary；
Task Count；
Agent Roles；
Model Mix；
Cost / Time Saved；
Deliverables Preview；
Evidence Snapshot；
Replay Timeline；
Export Demo Report；
Export Video Script。
26.7 新增关键页面
CEO Agent Switchboard
active CEO；
candidate CEOs；
conformance status；
switch approval；
rollback；
switch history。
Model Policy Center
Agent → Model；
Product Line → Model；
Task Type → Model；
cost tier；
quality tier；
CEO proposed changes；
Founder approval。
Workflow Studio
product line workflow；
stage-level agent / skill / runtime / model；
single vs multi-agent；
cost estimate；
risk estimate；
change history；
CEO proposed workflow changes。
Intake Inbox
OS UI 输入；
CEO chat 同步项；
classification；
promote / ignore / cleanup；
TTL。
Opportunity Radar
opportunities；
signals；
confidence；
evidence；
Founder Review；
Opportunity-to-PRD pipeline。
PRD Room
Requirement Brief；
clarifying questions；
PRD Writer Provider；
PRD draft；
Founder comments；
Implementation Plan；
Work Queue tasks。
Company Context Map
Founder principles；
business rules；
product lines；
decisions；
customer understanding；
lessons。
Learning Loop
failures；
root causes；
fix type；
applied changes；
next-run improvement。
27. AI Army Replay Engine
27.1 目标
把真实 Work Queue event log 转成可展示的运行回放。
27.2 P0
实现：
event log → timeline JSON；
tools/os-replay build；
replay JSON；
Markdown summary。
27.3 P1
实现：
UI replay timeline；
export report；
build-in-public report。
27.4 P2
实现：
video script；
storyboard；
social post；
investor demo export；
short video material package。
28. Product Line Support
OS 底座必须支持多产品线。
产品线包括：
SaaS / 工具；
AI Music；
AI Short Drama；
AI Novel；
Amazon / 跨境电商；
Independent Site；
Media Matrix；
GitHub / Public Build；
OS Core Development。
每个产品线需要：
product_line:
  id:
  goal:
  lead_agent:
  available_capabilities:
  available_skills:
  allowed_runtimes:
  allowed_models:
  workflow_template:
  deliverable_types:
  cost_budget:
  review_policy:
  evidence_policy:
  context_pack_policy:
v0.47 做 schema / UI placeholder。v0.50+ 做真实多产品线并行。
29. 版本路线
v0.47 — OS Control Plane MVP
目标：从手工流程变成可运行的最小 OS 控制平面。
P0：
Work Queue Engine；
Runtime Adapter Base；
local_script_adapter formalization；
codex_adapter wrapper；
Runtime Invocation Authenticity Gate；
Handoff Packet Schema；
Audit Packet Schema；
Canonical Repo Gate；
CLI；
Tests；
Founder Control Center Lite skeleton；
CEO Agent Provider Registry；
Model Profile Registry；
Intake Record Schema；
Native vs OS-Governed Action 字段；
Capability Registry schema；
Product Line Workflow schema；
Company Context schema；
Learning Event schema。
P1：
Codex Adapter smoke test；
Claude Code readiness；
Registry status update flow；
Cost Ledger MVP；
Audit Packet UI；
Intake workflow；
CEO switch preview；
Model Policy UI；
Workflow Studio UI；
Context candidate approval；
Learning event review。
P2：
persistent worker 留接口；
multi-runtime 留接口；
AI Army Live View 留接口；
workflow optimization 留接口；
model optimization 留接口。
v0.48 — Capability & Skill Supply Chain
P0：
Skill Manifest Schema；
Capability Registry；
tools/os-skill list/show/lookup/validate；
agent_compatibility matrix；
model_compatibility matrix；
test_fixture / production_skill 区分。
P1：
skill import candidate flow；
external skill security review；
product line capability gap detection；
capability mapping UI；
marketplace reference registry。
P2：
Skill Router；
Context Pack Builder；
marketplace search；
OpenClaw / Hermes / Tencent / Claude skill ecosystem adapter；
auto capability recommendation。
v0.49 — Async Work Queue Lite
P0：
os-worker daemon lite；
poll inbox；
claim lease；
heartbeat；
timeout recovery；
retry。
P1：
multiple workers；
runtime adapter dispatch；
model policy dispatch；
queue status CLI；
audit log search；
waiting_review notification。
P2：
Cron trigger；
Event trigger；
background work while Founder chats with CEO；
UI live status；
multi-runtime parallel。
v0.50 — Multi-Runtime / Multi-Workflow Trial
P0：
local_script + Codex 顺序执行；
two work items；
two audit packets。
P1：
local_script + Codex + Claude Code；
SaaS workflow；
AI Novel workflow；
AI Music workflow；
cost aggregation；
runtime comparison。
P2：
OpenClaw readiness；
OpenClaw adapter smoke test；
multi-work parallel；
runtime auto-selection；
workflow auto-selection；
model auto-selection。
v0.51 — PRD-to-Execution Pipeline
P0：
PRD template；
PRD quality gate；
P0/P1/P2 checker；
task extraction。
P1：
Codex plan adapter；
Claude plan adapter；
implementation plan review；
PRD → Work Queue converter；
Opportunity → PRD flow。
P2：
Founder goal → PRD → Plan → Work Queue → Runtime → Audit → Memory 自动闭环。
v0.52 — Founder Control Center & AI Army UI
P0：
Dashboard shell；
Today Command；
Work Queue Board；
Review Inbox；
Runtime Adapter Status；
Cost Summary；
Deliverables List；
CEO Agent Switchboard placeholder；
Model Policy Center placeholder；
Workflow Studio placeholder；
Intake Inbox placeholder；
Company Context Map placeholder；
Learning Loop placeholder。
P1：
AI Army Live View；
Mission Flow；
Agent Lanes；
Runtime Lanes；
Product Line Lanes；
Timeline；
Cost by runtime / model / product line；
Audit Packet Viewer。
P2：
Investor Demo Mode；
Replay Timeline；
Auto Demo Report；
Video Script Export；
Public-safe Evidence Package。
30. Codex Implementation Epics
Epic 1 — Project Structure & AGENTS.md
创建：
AGENTS.md
os_core/
tools/adapters/
schemas/
tests/
AGENTS.md 包含：
canonical repo rule；
no direct CEO execution rule；
Native vs OS-Governed distinction；
forbidden paths；
no commit / no push unless approved；
private boundary；
runtime authenticity gate；
staged gate rule；
test requirements；
model policy rule；
workflow change rule。
验收：
Codex 每次任务前读取 AGENTS.md；
不含本机绝对路径；
指向 private/runtime/local-paths.yaml；
public/private boundary 明确。
Epic 2 — Work Queue Core
实现：
Work Queue state manager；
status transition；
audit log；
retry；
lease；
inspect；
CLI。
验收：
B1 local_script flow 不回退；
状态转换完整；
tests pass。
Epic 3 — Runtime Adapter Base + Local Script Adapter
实现：
base_adapter；
local_script_adapter；
adapter registry loader；
conformance test。
验收：
local_script 保持 verified_B1；
base adapter 可扩展。
Epic 4 — Codex Adapter Wrapper
实现：
codex_adapter.py；
handoff packet reader；
prompt builder；
codex exec invocation；
stdout/stderr/exit_code capture；
outbox writer；
audit evidence。
验收：
invocation_source = os_runtime_adapter；
used_ceo_skill = false；
ceo_executed_directly = false；
no git commit；
no git push；
forbidden paths block。
Epic 5 — Gates
实现：
canonical repo gate；
runtime invocation authenticity gate；
forbidden path gate；
no CEO direct execution gate；
public/private boundary gate；
official action gate；
model policy gate；
workflow change gate。
验收：
invalid case fail；
valid case pass；
adapter trials must call gates。
Epic 6 — Audit / Cost / Evidence
实现：
audit packet；
cost event；
evidence candidate；
memory candidate；
deliverable registry lite。
验收：
every work item produces audit；
cost summary works；
evidence candidate can be reviewed。
Epic 7 — CEO Provider + Intake
实现：
CEO provider registry；
CEO conformance schema；
intake record schema；
conversation sync placeholder；
Native vs OS-Governed fields。
验收：
UI can show active CEO；
intake item can be promoted to goal / task / context；
native chat not automatically official OS action。
Epic 8 — Model Policy + Workflow Composer
实现：
Model Profile Registry；
agent model policy；
product line model policy；
model change record；
product_line_workflow schema；
workflow template registry；
workflow change record。
验收：
Founder can configure model policy；
CEO can propose model change；
Founder can configure workflow；
CEO can propose workflow change；
all changes logged and rollbackable。
Epic 9 — Capability & Skill Supply Chain
实现：
capability registry；
skill schema；
tools/os-skill；
skill security review schema；
capability mapping。
验收：
skill lookup works；
capability gap can be recorded；
imported skill must be reviewed before production use。
Epic 10 — Company Context + Learning Loop
实现：
context schema；
context candidate；
learning event schema；
learning event CLI；
link to work_id；
UI placeholder。
验收：
failure can create learning candidate；
context can be approved；
next task can reference context pack policy。
Epic 11 — Opportunity + PRD Pipeline
实现：
opportunity card schema；
opportunity status；
opportunity review；
Requirement Brief schema；
PRD Writer Provider Registry；
PRD Room placeholder；
tools/os-prd validate / extract-tasks。
验收：
approved opportunity can become PRD Brief；
PRD can become task draft；
Founder review required before execution。
Epic 12 — Founder Control Center UI
实现：
frontend EPERM issue handling；
dashboard shell；
Today Command；
Work Queue Board；
Review Inbox；
Runtime Adapter Status；
Cost Summary；
Deliverables List；
CEO Agent Switchboard placeholder；
Model Policy Center placeholder；
Workflow Studio placeholder；
Intake Inbox placeholder；
Opportunity Radar placeholder；
PRD Room placeholder；
Company Context Map placeholder；
Learning Loop placeholder。
验收：
frontend can run；
data can load from local files / JSON；
no private leakage；
not just file list；
Founder can see tasks, runtime, cost, model, workflow, review.
Epic 13 — AI Army Live + Replay
实现：
event log → timeline JSON；
AI Army Live View skeleton；
Replay Timeline skeleton；
export markdown report；
investor demo placeholder。
验收：
one run can be replayed；
shows goals → tasks → agents → models → outputs → costs；
public-safe mode hides private info。
Epic 14 — Tests & Release Readiness
实现：
unit tests；
smoke tests；
CLI tests；
UI smoke tests；
private leak test；
no local absolute path test；
no git commit / push by adapter test；
no fake adapter invocation test；
model policy test；
workflow change test。
验收：
all P0 tests pass；
private/ not tracked；
no unauthorized path write；
no fake adapter invocation。
31. Review / QA Model
31.1 Codex Self-Check
Codex 每个 Epic 完成后必须输出：
changed files；
test commands；
test results；
audit packet；
known limitations；
next recommended step。
31.2 Claude Code Review
Claude Code 审查：
architecture consistency；
code maintainability；
security / path boundary；
no fake adapter invocation；
tests quality；
UI information architecture quality；
model policy consistency；
workflow composer consistency。
Claude 先输出 Review，不直接改。需要改动时，单独走 Work Queue。
31.3 Hermes Review
Hermes 负责：
是否符合 Founder 目标；
是否越界；
是否要生成 memory / evidence；
是否进入下一阶段；
是否需要 Founder approval；
CEO 角色是否越权；
model / workflow 变更是否在授权范围内。
Hermes 不直接修代码。
31.4 Founder Review
Founder 看：
阶段是否达成；
UI 是否符合产品愿景；
是否进入下一版本；
是否允许 commit / push / public release；
是否调整方向；
是否切换 CEO；
是否授权 CEO 调整模型或工作流。
32. 禁止项
全局禁止：
Codex 自行 commit；
Codex 自行 push；
Codex 修改 private/；
Codex 修改 .git/；
Codex 修改 memory-system/；
Codex 修改 production os-skills，除非该 Epic 明确允许；
Codex 修改 docs/adr/，除非是明确 ADR 任务；
Codex 直接升级 runtime registry 状态；
Codex 直接修改 model policy 为生产配置，除非任务明确允许；
Codex 直接修改 workflow policy 为生产配置，除非任务明确允许；
Hermes 直接执行代码任务并冒充 executor；
OpenClaw 被当作 OS Work Queue；
UI 展示假数据冒充真实运行；
public docs 写本机绝对路径；
外部 Skill 未审查进入 production；
把 ComfyUI / TTS / 视频工具塞入 OS Core。
33. Definition of Done
v0.47–v1.0 Core Substrate 完成标准：
Work Queue Engine 可稳定创建、执行、Review 任务；
Runtime Adapter Base 可用；
Codex Adapter 真实通过 wrapper 调用；
Claude Code Adapter readiness 通过；
OpenClaw Adapter readiness 通过或明确 blocked；
Runtime Invocation Authenticity Gate 可阻止假调用；
CEO Agent 可替换，有 Switchboard 和 conformance test；
OS UI 和 CEO chat 输入能进入 Intake 分流；
Native Agent Mode 与 OS-Governed Mode 区分清楚；
Founder 可以配置模型策略；
CEO Agent 可以在授权范围内提出或调整模型策略；
Founder 可以配置产品线工作流；
CEO Agent 可以在授权范围内提出或调整工作流；
Skill / Capability Supply Chain 可登记能力来源；
外部 Skill 引入有安全审查；
Company Context Graph 可记录 Founder 原则、业务规则、产品线知识、历史决策；
Learning Loop 可把失败变成规则、工具、Skill、Context、Model、Workflow 或测试改进；
Opportunity Discovery 可以进入 PRD Pipeline；
PRD Protocol CLI 可用；
Skill Protocol CLI 可用；
Cost Ledger 可记录任务成本、模型成本、产品线成本；
Audit Packet 可追踪每个任务；
Founder Control Center UI 可看任务、成本、Adapter、Model、Workflow、Review、Deliverables；
AI Army Live View 可展示任务流转；
Replay Engine 可输出运行时间线；
所有 public docs 不含本机绝对路径；
private/ 不被 git tracked；
Codex / Claude / OpenClaw 均不绑定 OS Core；
Founder 可以下达多线目标；
CEO Agent 可以澄清、拆解和 Review；
后台 Runtime 可以接单执行；
Founder 不再需要做人肉搬运工。
34. English Implementation Handoff for Codex / Claude Code
34.1 Product Goal
Build AI Company OS Core Substrate v0.47–v1.0.
AI Company OS is not an agent framework.It is the governance and operating layer above agent frameworks.
The system must allow a Founder to work through a replaceable CEO Agent while the OS manages:
Work Queue;
Runtime Adapters;
Planning Adapters;
Model Policy;
Workflow Composer;
Quality Gates;
Audit Packets;
Cost Ledger;
Capability & Skill Supply Chain;
Company Context;
Evidence / Memory;
Learning Loop;
Founder Control Center UI.
34.2 Core Architecture
Founder→ CEO Agent Provider Layer→ Intent Intake / Requirement Clarification / Opportunity Review→ AI Company OS Core→ Work Queue + State Machine + Quality Gate + Audit + Cost + Context + Skill + Model + Workflow→ Runtime Adapter Interface / Planning Adapter Interface / Tool Adapter Interface→ local_script / Codex / Claude Code / OpenClaw / GPT / Cursor / Copilot / future adapters
34.3 Mandatory Rules
Do not let the CEO Agent impersonate executor.
Any official OS action requires:
Goal or Task Record;
Work Queue entry;
Handoff Packet;
Runtime Adapter or CEO Review record;
Audit Packet;
Review outcome;
Evidence / Memory / Asset decision.
Native agent actions are allowed, but they are not official OS actions unless they pass OS-Governed Mode.
34.4 Model Policy Rule
The OS must support configurable model selection by Founder.
Model selection can be defined by:
agent;
runtime;
product line;
task type;
workflow stage.
CEO Agent can propose or adjust model policy only within Founder authorization.
All model changes must be recorded, reviewable, cost-aware, and rollbackable.
34.5 Workflow Composer Rule
The OS must support configurable product line workflows.
Founder can configure workflows manually.CEO Agent can propose or adjust workflows within Founder authorization.
Workflows must record:
stages;
agent / skill / runtime / model per stage;
review policy;
cost policy;
risk policy;
change history;
rollback option.
34.6 First Implementation Requirement
Do not write code immediately.
First output an Implementation Plan covering:
proposed directory structure;
existing files to read;
files to create;
files to modify;
forbidden paths;
test plan;
epic-by-epic implementation order;
risks / blockers;
questions requiring Founder approval.
34.7 First Implementation Epics
Epic 1 — Project Structure & AGENTS.mdEpic 2 — Work Queue CoreEpic 3 — Runtime Adapter Base + Local Script AdapterEpic 4 — Codex Adapter WrapperEpic 5 — GatesEpic 6 — Audit / Cost / EvidenceEpic 7 — CEO Provider + IntakeEpic 8 — Model Policy + Workflow ComposerEpic 9 — Capability & Skill Supply ChainEpic 10 — Company Context + Learning LoopEpic 11 — Opportunity + PRD PipelineEpic 12 — Founder Control Center UIEpic 13 — AI Army Live + ReplayEpic 14 — Tests & Release Readiness
34.8 Hard Restrictions
Codex must not:
commit;
push;
modify private/;
modify .git/;
modify memory-system/;
upgrade runtime registry status;
change production model policy without approval;
change production workflow policy without approval;
treat Hermes / OpenClaw / Codex / Claude as OS Core;
write local absolute paths into public docs;
bypass Work Queue;
call runtime outside adapter wrapper;
create fake adapter invocation.
34.9 Required Evidence
Every implementation step must output:
changed files;
test commands;
test results;
audit packet;
known limitations;
next recommended step.
34.10 Definition of Done
The Core Substrate is done when:
Work Queue works;
Runtime Adapter Base works;
Codex Adapter is invoked through wrapper;
Runtime Invocation Authenticity Gate blocks fake calls;
CEO Agent is replaceable;
Intake Sync exists;
Model Policy exists;
Workflow Composer exists;
Skill / Capability Supply Chain exists;
Company Context exists;
Learning Loop exists;
Opportunity-to-PRD Pipeline exists;
Cost Ledger exists;
Founder Control Center UI exists;
AI Army Live View exists;
Audit / Evidence / Memory pipeline works;
Founder no longer needs to manually move information between agents.
---
# 35. Codex 第一条任务
给 Codex 的第一条任务必须是 Planning，不是 Coding：
```text
You are implementing AI Company OS Core Substrate v0.47–v1.0.
Read the full PRD.
Do not modify files yet.
Do not commit.
Do not push.
First output an Implementation Plan.
The plan must include:
1. proposed directory structure;
2. existing files to read;
3. files to create;
4. files to modify;
5. forbidden paths;
6. test plan;
7. epic-by-epic implementation order;
8. risks / blockers;
9. questions requiring Founder approval.
Pay special attention to:
- replaceable CEO Agent;
- Native Agent Mode vs OS-Governed Mode;
- Runtime Invocation Authenticity Gate;
- Model Policy;
- Product Line Workflow Composer;
- Opportunity-to-PRD Pipeline;
- Skill / Capability Supply Chain;
- Company Context Graph;
- Learning Loop;
- Founder Control Center UI.
Do not write code in this planning step.