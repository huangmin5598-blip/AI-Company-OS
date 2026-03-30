# Task Panel Skill

基于飞书多维表格的任务面板管理技能。

## 功能

- 创建任务
- 更新任务状态
- 查询任务列表
- 任务升级/阻塞处理

## 使用前提

需要先创建飞书多维表格（bitable），获取：
- `app_token`
- `table_id`

## 工具依赖

使用 `feishu_bitable` 工具集：
- `feishu_bitable_create_record` - 创建任务
- `feishu_bitable_update_record` - 更新任务
- `feishu_bitable_list_records` - 查询任务

## 字段映射

| 字段名 | field_id | 类型 |
|--------|----------|------|
| 任务ID | fldA4HSWcf | Text |
| 项目 | fldEnLQT28 | Text |
| 任务标题 | fldyeNp4U5 | Text |
| 任务类型 | fld0t9wvxm | SingleSelect |
| 优先级 | fldIJYA0Pf | SingleSelect |
| 状态 | fldywBeZSM | SingleSelect |
| 发起人 | fldTtc9fbd | Text |
| 负责人 | fld4jLF0AE | Text |
| 截止时间 | fldJsPZQnV | DateTime |
| 交付链接 | fldNwZMnHf | URL |
| 阻塞原因 | fldiBR6bbq | Text |
| 升级状态 | fldODnXnXW | Checkbox |
| 验收结果 | fldCXScjBe | SingleSelect |

## 任务类型选项

研发、测试、内容、研究、渠道、复盘

## 优先级选项

P1、P2、P3

## 状态选项

待创建、待派发、已派发、执行中、待验收、已完成、已阻塞、已升级

## 验收结果选项

通过、不通过、需修改

## 示例

### 创建任务

```
app_token: "Snxrb3p58aEGDksVEBZcQNYEn9g"
table_id: "tbl3uKOl4ZzjkowT"
fields: {
  "任务ID": "T001",
  "项目": "表情包项目",
  "任务标题": "开发表情包生成页面",
  "任务类型": "研发",
  "优先级": "P1",
  "状态": "待派发",
  "发起人": "lead-st负责人": "buildericker",
  "-core",
  "截止时间": "2026-03-15"
}
```

### 更新状态

```
app_token: "Snxrb3p58aEGDksVEBZcQNYEn9g"
table_id: "tbl3uKOl4ZzjkowT"
record_id: "recxxx"
fields: {
  "状态": "执行中"
}
```

### 查询任务

```
app_token: "Snxrb3p58aEGDksVEBZcQNYEn9g"
table_id: "tbl3uKOl4ZzjkowT"
```

---

**维护者**: Tiger
**版本**: 1.0
**创建时间**: 2026-03-11
