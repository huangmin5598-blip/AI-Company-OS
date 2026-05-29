# Launch Brief — LR-001

> Amazon 利润体检报告 — 服务型产品

---

## 1. 产品基础信息

| 字段 | 值 |
|:----|:---|
| `launch_run_id` | LR-001 |
| `product_name` | Amazon 利润体检报告 |
| `product_type` | 服务（报告 + 诊断） |
| `product_line` | ai-seller-finance |
| `version` | v0.1（MVP） |
| `launch_date` | 2026-05-29 |

## 2. 目标用户

| 字段 | 值 |
|:----|:---|
| `target_user` | 月营业额 ¥50–200 万的 Amazon 中国跨境卖家 |
| `pain_point` | 算不清真实利润、广告吃掉净利润、库存现金流黑洞、多站点数据孤岛、凭直觉做决策 |
| `user_scale` | 估算 10 万+ 活跃卖家有利润分析需求 |

## 3. 产品价值

| 字段 | 值 |
|:----|:---|
| `offer` | 上传 Settlement CSV，1 分钟生成 9 章利润体检报告 |
| `differentiator` | 本地处理不上传、广告 ROI 算到净利润层、提前 30 天现金流预警 |
| `proof_points` | 典型卖家发现 ¥15-30 万隐性利润流失；40-60% 卖家广告费侵蚀净利润 |

## 4. 定价与转化

| 字段 | 值 |
|:----|:---|
| `price_tiers` | 免费体检（1 次）→ ¥99/月（月度监控）→ ¥499/月（年度经营） |
| `sample_asset` | `launch-pipeline/runs/LR-001-amazon-profit-health-check/sample-report.md` |
| `cta` | 免费生成利润体检报告 |
| `conversion_goal` | 体验官招募 → 付费转化 |

## 5. 销售与分发

| 字段 | 值 |
|:----|:---|
| `distribution_channel` | 自有独立站（profit.ai-company-os.com）+ 小红书/微信社群冷启动 |
| `cold_start_copy` | "你的 Amazon 店铺，到底赚了多少？" ← Hero 标题 |
| `target_platform` | profit.ai-company-os.com |
| `success_metric` | 10 个体验官注册 → 5 份真实报告生成 → 2 个付费转化 |
| `next_promotion_action` | 小红书图文：卖家真实利润对比案例 |

## 6. 部署

| 字段 | 值 |
|:----|:---|
| `deployment_target` | Cloudflare Pages |
| `deployment_domain` | profit.ai-company-os.com |
| `environment_vars` | 无（纯静态页） |

## 7. 额外说明

```
- 销售页已部署，SSL 签发中
- 产品本身是本地脚本，尚需 Web 化
- 首批通过免费体验报告获取种子用户
```
