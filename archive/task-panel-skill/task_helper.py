#!/usr/bin/env python3
"""
Task Panel Helper - 任务面板辅助脚本
用于 OpenClaw Agent 快速操作飞书任务面板
"""

# 固定配置
APP_TOKEN = "Snxrb3p58aEGDksVEBZcQNYEn9g"
TABLE_ID = "tbl3uKOl4ZzjkowT"

# 字段ID映射
FIELDS = {
    "任务ID": "fldA4HSWcf",
    "项目": "fldEnLQT28",
    "任务标题": "fldyeNp4U5",
    "任务类型": "fld0t9wvxm",
    "优先级": "fldIJYA0Pf",
    "状态": "fldywBeZSM",
    "发起人": "fldTtc9fbd",
    "负责人": "fld4jLF0AE",
    "截止时间": "fldJsPZQnV",
    "交付链接": "fldNwZMnHf",
    "阻塞原因": "fldiBR6bbq",
    "升级状态": "fldODnXnXW",
    "验收结果": "fldCXScjBe",
}

# 字段ID到名称的反向映射
FIELDS_REVERSE = {v: k for k, v in FIELDS.items()}


def create_task_record(task_info: dict) -> dict:
    """
    创建任务记录
    
    参数:
        task_info: 任务信息字典
    
    返回:
        feishu_bitable_create_record 所需的参数
    """
    fields = {}
    
    # 文本字段
    text_fields = ["任务ID", "项目", "任务标题", "发起人", "负责人", "阻塞原因"]
    for field in text_fields:
        if field in task_info:
            fields[FIELDS[field]] = task_info[field]
    
    # 单选字段
    select_fields = ["任务类型", "优先级", "状态", "验收结果"]
    for field in select_fields:
        if field in task_info:
            fields[FIELDS[field]] = task_info[field]
    
    # URL字段
    if "交付链接" in task_info:
        url = task_info["交付链接"]
        if isinstance(url, str):
            fields[FIELDS["交付链接"]] = {"text": url, "link": url}
    
    # 时间字段 (毫秒时间戳)
    if "截止时间" in task_info:
        # 支持多种格式
        import datetime
        dt = task_info["截止时间"]
        if isinstance(dt, str):
            # 尝试解析日期字符串
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"]:
                try:
                    dt = datetime.datetime.strptime(dt, fmt)
                    fields[FIELDS["截止时间"]] = int(dt.timestamp() * 1000)
                    break
                except:
                    pass
        elif isinstance(dt, datetime.datetime):
            fields[FIELDS["截止时间"]] = int(dt.timestamp() * 1000)
    
    # 复选框字段
    if "升级状态" in task_info:
        fields[FIELDS["升级状态"]] = task_info["升级状态"]
    
    return {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "fields": fields
    }


def update_task_status(record_id: str, new_status: str) -> dict:
    """
    更新任务状态
    
    参数:
        record_id: 记录ID
        new_status: 新状态
    
    返回:
        feishu_bitable_update_record 所需的参数
    """
    return {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "record_id": record_id,
        "fields": {
            FIELDS["状态"]: new_status
        }
    }


# 示例用法
if __name__ == "__main__":
    # 示例：创建任务
    example_task = {
        "任务ID": "T001",
        "项目": "表情包项目",
        "任务标题": "开发表情包生成页面",
        "任务类型": "研发",
        "优先级": "P1",
        "状态": "待派发",
        "发起人": "lead-sticker",
        "负责人": "builder-core",
        "截止时间": "2026-03-15"
    }
    
    result = create_task_record(example_task)
    print("创建任务参数:")
    print(result)
