# 部署与接线手册

## 1. 总体接线顺序
1. 先验证 OpenClaw 本体可运行。
2. 接入 Feishu，只绑定 CEO + 各项目主管。
3. 配置 MiniMax 2.5，验证 CEO 与一个项目主管能正常响应。
4. 配置阿里云 Coding Plan，验证 architect-core / builder-core。
5. 配置本地 Qwen 与 DeepSeek 的 OpenAI-compatible 接口。
6. 最后再启用短剧、小说三段式与 Opportunity Lab。

## 2. Feishu 接线
- 创建 7 个内部机器人：CEO + 6 个项目主管。
- 将真实 peer / bot 标识替换到 configs/bindings.json5。
- 不要为后台 Agent 创建独立飞书入口。

## 3. MiniMax 2.5 接线
- 在环境变量中写入 MINIMAX_API_KEY。
- 将 configs/models.json5 中 minimax.base_url 改为你的真实入口。
- CEO 与各项目主管统一使用 minimax_general。

## 4. 阿里云 Coding Plan 接线
- 在环境变量中写入 DASHSCOPE_API_KEY。
- 将 dashscope.base_url 改为你的真实入口。
- 共享研发中心统一使用 aliyun_coding。
- 注意：Coding Plan 主要作为交互式研发入口，避免拿它做大规模后台自动批处理。

## 5. 本地 Qwen / DeepSeek 接线
- 让两个本地服务都暴露 OpenAI-compatible /v1 接口。
- 建议分别绑定到不同端口，例如：
  - Qwen: http://127.0.0.1:8001/v1
  - DeepSeek: http://127.0.0.1:8002/v1
- 在 configs/models.json5 中确认 base_url。
- 如果本地接口不校验 key，可在环境变量中给占位值。

## 6. 短剧与小说链路接线
- lead-shortdrama 在飞书前台；story-fusion-agent、analytics-shortdrama、ip-transfer-agent、novel-* 默认后台。
- 你与 ChatGPT 的主创部分继续保持人工协同。
- novel-planner 使用 Qwen；novel-writer 使用 DeepSeek；novel-editor 使用 Qwen。

## 7. YouTube 数据分析接线
- 先只做 analytics-only：公开视频信息、标题、评论与基础数据整理。
- 等自有频道数据和 API 准备好，再扩到更完整的分析报表。

## 8. 上线顺序建议
- 第 1 周：CEO、lead-shortdrama、lead-grading、architect-core、builder-core
- 第 2 周：qa-tech-core、qa-business-core、creative-lab、ads-lab
- 第 3 周：trend-scout、product-gap-scout、social-pain-scout、opportunity-synthesizer
- 第 4 周：novel-planner、novel-writer、novel-editor、analytics-shortdrama、ip-transfer-agent

## 9. 最重要的注意事项
- 不要一次性全开所有 Agent。
- 不要一开始就自动评论/自动互动。
- 不要让多个项目共享 secrets、会话、知识库与长期记忆。
- 先把组织和路由跑通，再逐步增加自动化。
