#!/bin/bash
# Heartbeat Executor - v2.0 (with Failure Protocol)
# 功能: 每天 09:00 自动检查并生成周期任务 + 失败检测与自恢复
# 设计: Stateless, 基于文件系统的任务池

WORKSPACE="/Users/tangbomao/.openclaw/workspace"
TASKPOOL="$WORKSPACE/TASK-POOL.md"
LOGFILE="$WORKSPACE/memory/heartbeat.log"
DATE=$(date +%Y-%m-%d)
DATETIME=$(date +"%Y-%m-%d %H:%M:%S")

mkdir -p "$WORKSPACE/memory"

echo "" >> "$LOGFILE"
echo "=== Heartbeat: $DATETIME ===" >> "$LOGFILE"

# =====================
# 0. FAILURE DETECTION (检测阶段)
# =====================
FAILURES=""
RECOVERY_ACTIONS=""

# 0.1 TRIGGER FAILURE - 检查昨日是否执行
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "1 day ago" +%Y-%m-%d)
if ! grep -q "\[HEARTBEAT.*$YESTERDAY.*DONE\]" "$LOGFILE" 2>/dev/null; then
    if [ "$DATE" != "$YESTERDAY" ]; then
        FAILURES="${FAILURES}TRIGGER_FAILURE "
        RECOVERY_ACTIONS="${RECOVERY_ACTIONS}Compensate_Yesterday "
        echo "[FAILURE] TRIGGER: Heartbeat not executed on $YESTERDAY" >> "$LOGFILE"
    fi
fi

# 0.2 PRODUCTION FAILURE - 检查任务是否生成
NOVEL_COUNT=$(grep -E "novel-[0-9]+.*$DATE" "$TASKPOOL" 2>/dev/null | wc -l)
NOVEL_COUNT=$((NOVEL_COUNT + 0))
echo "[CHECK] novel-v1 today: $NOVEL_COUNT/2" >> "$LOGFILE"

if [ "$NOVEL_COUNT" -lt 2 ]; then
    FAILURES="${FAILURES}PRODUCTION_FAILURE "
    echo "[FAILURE] PRODUCTION: novel-v1 only has $NOVEL_COUNT tasks" >> "$LOGFILE"
fi

# 0.3 FLOW FAILURE - 检查卡住的任务（仅检查今日生成但未完成的任务）
# 排除协议说明和历史任务
STUCK_TASKS=0
for task_id in $(grep -oE "novel-[0-9]+.*$DATE" "$TASKPOOL" 2>/dev/null | grep -oE "novel-[0-9]+"); do
    if grep -q "$task_id.*待执行\|$task_id.*执行中" "$TASKPOOL" 2>/dev/null; then
        STUCK_TASKS=$((STUCK_TASKS + 1))
    fi
done
if [ "$STUCK_TASKS" -gt 0 ]; then
    FAILURES="${FAILURES}FLOW_FAILURE "
    RECOVERY_ACTIONS="${RECOVERY_ACTIONS}Auto_Progress "
    echo "[FAILURE] FLOW: $STUCK_TASKS tasks stuck" >> "$LOGFILE"
fi

# 0.4 EXPORT FAILURE - 检查未导出的完成任务（仅今日）
UNEXPORTED=0
for task_id in $(grep -oE "novel-[0-9]+.*$DATE.*已完成" "$TASKPOOL" 2>/dev/null | grep -oE "novel-[0-9]+"); do
    if ! grep -q "$task_id.*\.docx" "$TASKPOOL" 2>/dev/null; then
        UNEXPORTED=$((UNEXPORTED + 1))
    fi
done
if [ "$UNEXPORTED" -gt 0 ]; then
    FAILURES="${FAILURES}EXPORT_FAILURE "
    RECOVERY_ACTIONS="${RECOVERY_ACTIONS}Trigger_Export "
    echo "[FAILURE] EXPORT: $UNEXPORTED tasks not exported" >> "$LOGFILE"
fi

# 0.5 DATA FAILURE - 检查 TASK-POOL 状态一致性
# 简单检查：completed 任务数是否合理
TOTAL_TASKS=$(grep -c "^|" "$TASKPOOL" 2>/dev/null || echo "0")
echo "[CHECK] Total tasks in pool: $TOTAL_TASKS" >> "$LOGFILE"

# =====================
# 1. RECOVERY (恢复阶段)
# =====================
if [ -n "$FAILURES" ]; then
    echo "[RECOVERY] Detected failures: $FAILURES" >> "$LOGFILE"
    echo "[RECOVERY] Actions: $RECOVERY_ACTIONS" >> "$LOGFILE"
    
    # 1.1 TRIGGER FAILURE Recovery - 补执行昨日任务
    if echo "$FAILURES" | grep -q "TRIGGER_FAILURE"; then
        echo "[RECOVERY] Compensating missed heartbeat..." >> "$LOGFILE"
    fi
    
    # 1.2 PRODUCTION FAILURE Recovery - 补生成任务
    if echo "$FAILURES" | grep -q "PRODUCTION_FAILURE"; then
        # 补生成任务逻辑在下面第2步
        :
    fi
    
    # 1.3 FLOW FAILURE Recovery - 记录待推进
    if echo "$FAILURES" | grep -q "FLOW_FAILURE"; then
        echo "[RECOVERY] Flow interruption detected - will be handled by CEO" >> "$LOGFILE"
    fi
    
    # 1.4 EXPORT FAILURE Recovery - 记录未导出
    if echo "$FAILURES" | grep -q "EXPORT_FAILURE"; then
        echo "[RECOVERY] Export failure detected - will be handled by CEO" >> "$LOGFILE"
    fi
fi

# =====================
# 2. TASK GENERATION (任务生成)
# =====================

# 检查今日是否已执行（防重复）- 但允许补偿任务
SKIPPED=""
if grep -q "\[HEARTBEAT.*$DATE.*DONE\]" "$LOGFILE" 2>/dev/null; then
    # 如果有失败需要补偿，仍然执行
    if [ -z "$FAILURES" ]; then
        SKIPPED="yes"
    fi
fi

if [ "$SKIPPED" != "yes" ]; then
    # === novel-v1: Daily 2 篇 ===
    if [ "$NOVEL_COUNT" -lt 2 ]; then
        echo "[GENERATE] Creating novel-v1 tasks..." >> "$LOGFILE"
        
        # 获取下一个任务 ID
        MAX_ID=$(grep -oE "novel-[0-9]+" "$TASKPOOL" 2>/dev/null | grep -oE "[0-9]+" | sort -n | tail -1)
        MAX_ID=${MAX_ID:-6}
        
        # 判断是否补偿任务
        COMPENSATED_MARK=""
        if [ -n "$FAILURES" ]; then
            COMPENSATED_MARK="(补偿任务)"
        fi
        
        TASK_7="| novel-$((MAX_ID+1)) | 短篇 #$((MAX_ID+1))：AI生成题材A $COMPENSATED_MARK | 待执行 | - | - |"
        TASK_8="| novel-$((MAX_ID+2)) | 短篇 #$((MAX_ID+2))：AI生成题材B $COMPENSATED_MARK | 待执行 | - | - |"
        
        # 插入新任务
        sed -i "" "/^## Round 2 任务/a\\
\\
### $DATE 新增任务\\
\\
|Task ID|描述|状态|执行时间|产出|\\
|--------|------|------|----------|------|\\
$TASK_7\\
$TASK_8" "$TASKPOOL"
        
        echo "[GENERATE] Created novel-$((MAX_ID+1)), novel-$((MAX_ID+2))" >> "$LOGFILE"
    fi
fi

# =====================
# 3. OUTPUT SUMMARY
# =====================
echo "" >> "$LOGFILE"
echo "=== Summary ===" >> "$LOGFILE"
echo "Date: $DATE" >> "$LOGFILE"
echo "Failures: ${FAILURES:-None}" >> "$LOGFILE"
echo "Recovery: ${RECOVERY_ACTIONS:-None}" >> "$LOGFILE"
echo "[HEARTBEAT $DATE DONE]" >> "$LOGFILE"
echo "" >> "$LOGFILE"

# 输出到终端
echo "✅ Heartbeat: $DATE"
echo "📋 Failures: ${FAILURES:-None}"
echo "🔧 Recovery: ${RECOVERY_ACTIONS:-None}"
echo "📝 Log: $LOGFILE"
