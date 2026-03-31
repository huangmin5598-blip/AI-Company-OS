# OpenClaw Task Panel Skill

基于飞书多维表格的任务面板管理技能，用于 AI 公司多项目任务管理。

## 功能

- 创建任务
- 更新任务状态
- 查询任务列表
- 任务升级/阻塞处理

## 使用前提

1. 飞书开放平台应用权限
2. 已创建飞书多维表格

## 配置

### 1. 创建飞书多维表格

在飞书中创建多维表格，添加以下字段：

| 字段名 | 类型 | 选项 |
|--------|------|------|
| 任务ID | 文本 | - |
| 项目 | 文本 | - |
| 任务标题 | 文本 | - |
| 任务类型 | 单选 | 研发、测试、内容、研究、渠道、复盘 |
| 共享中心 | 文本 | - |
| 优先级 | 单选 | P1、P2、P3 |
| 状态 | 单选 | 待创建、待派发、已派发、执行中、待验收、待修改、已完成、已阻塞、已升级 |
| 发起人 | 文本 | - |
| 负责人 | 文本 | - |
| 截止时间 | 日期 | - |
| 交付链接 | 链接 | - |
| 阻塞原因 | 文本 | - |
| 升级状态 | 复选框 | - |
| 验收结果 | 单选 | 通过、不通过、需修改 |

### 2. 获取配置信息

从飞书多维表格 URL 获取：
- `app_token`: URL 中的 `app_token` 参数
- `table_id`: URL 中的 `table` 参数

### 3. 配置 Skill

在 OpenClaw 中配置 bitable 工具权限。

## 字段映射参考

```
app_token: "你的app_token"
table_id: "你的table_id"

字段映射：
- 任务ID: fldA4HSWcf
- 项目: fldEnLQT28
- 任务标题: fldyeNp4U5
- 任务类型: fld0t9wvxm
- 共享中心: fldIJYA0Pf
- 优先级: fldIJYA0Pf
- 状态: fldywBeZSM
- 发起人: fldTtc9fbd
- 负责人: fld4jLF0AE
- 截止时间: fldJsPZQnV
- 交付链接: fldNwZMnHf
- 阻塞原因: fldiBR6bbq
- 升级状态: fldODnXnXW
- 验收结果: fldCXScjBe
```

## 使用示例

### 创建任务

```python
feishu_bitable_create_record(
    app_token="你的app_token",
    table_id="你的table_id",
    fields={
        "任务ID": "T001",
        "项目": "表情包项目",
        "任务标题": "开发表情包生成页面",
        "任务类型": "研发",
        "优先级": "P1",
        "状态": "待派发",
        "发起人": "lead-sticker",
        "负责人": "builder-core",
        "截止时间": 1771454400000  # 毫秒时间戳
    }
)
```

### 更新状态

```python
feishu_bitable_update_record(
    app_token="你的app_token",
    table_id="你的table_id",
    record_id="记录ID",
    fields={
        "状态": "执行中"
    }
)
```

### 查询任务

```python
feishu_bitable_list_records(
    app_token="你的app_token",
    table_id="你的table_id"
)
```

## 任务状态流转

```
待创建 → 待派发 → 已派发 → 执行中 → 待验收
                                    ↓
                              待修改 (验收不通过)
                                    ↓
已阻塞 ← 已升级 ← 已完成
```

## 相关文档

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [飞书开放平台 - 多维表格](https://open.feishu.cn/document/ukTMukTMukTM/uADOwUjLwgDM14CM4ATN)

---

**作者**: Tiger  
**版本**: 1.0  
**更新**: 2026-03-11
