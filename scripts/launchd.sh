#!/usr/bin/env bash
# v0.18 — Launchd Management Script for AI Company OS
#
# Usage:
#   ./scripts/launchd.sh install     — Install and load the launchd plist
#   ./scripts/launchd.sh uninstall   — Unload and remove the launchd plist
#   ./scripts/launchd.sh status      — Show launchd job status + last run info
#   ./scripts/launchd.sh run         — Kickstart (run once immediately)
#   ./scripts/launchd.sh logs        — Show recent stdout + stderr
#   ./scripts/launchd.sh health      — Quick diagnostic: job, logs, DB
#
# Environment (override if needed):
#   AI_COMPANY_OS_ROOT  — Project root (default: auto-detect)

set -euo pipefail

# ── Auto-detect project root ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${AI_COMPANY_OS_ROOT:-"$(cd "$SCRIPT_DIR/.." && pwd)"}"
PLIST_SRC="$PROJECT_ROOT/config/launchd/com.ai-company-os.daily-operating-loop.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.ai-company-os.daily-operating-loop.plist"
LABEL="com.ai-company-os.daily-operating-loop"
LOG_DIR="$PROJECT_ROOT/logs/launchd"
LOG_OUT="$LOG_DIR/daily-operating-loop.out.log"
LOG_ERR="$LOG_DIR/daily-operating-loop.err.log"
DATABASE_PATH="$PROJECT_ROOT/backend/data/ai_company_os.db"

# ── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e " ${GREEN}✅${NC} $1"; }
warn() { echo -e " ${YELLOW}⚠️ $1${NC}"; }
fail() { echo -e " ${RED}❌${NC} $1"; }
info() { echo -e " ${CYAN}ℹ️  $1${NC}"; }

# ── Help ──────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
AI Company OS — Launchd Manager

Usage: $(basename "$0") <command>

Commands:
  install     Install and load the launchd plist (daily 09:00)
  uninstall   Unload and remove the launchd plist
  status      Show launchd job status + last run info
  run         Kickstart (run once immediately via launchctl)
  logs        Show recent stdout + stderr logs
  health      Quick diagnostic: job, logs, DB

Project root: $PROJECT_ROOT
EOF
    exit 1
}

# ── Commands ──────────────────────────────────────────────────────────

cmd_install() {
    echo "── Installing AI Company OS launchd job ──"

    # Ensure log directory exists
    mkdir -p "$LOG_DIR"
    ok "Log directory ready: $LOG_DIR"

    # Ensure plist source exists
    if [ ! -f "$PLIST_SRC" ]; then
        fail "Plist not found at: $PLIST_SRC"
        exit 1
    fi

    # Copy plist to LaunchAgents
    mkdir -p "$HOME/Library/LaunchAgents"
    cp "$PLIST_SRC" "$PLIST_DEST"
    ok "Plist copied to $PLIST_DEST"

    # Unload first in case of stale load
    launchctl unload "$PLIST_DEST" 2>/dev/null || true

    # Load
    launchctl load "$PLIST_DEST"
    ok "Launchd job loaded: $LABEL"
    echo ""
    echo "📅 Schedule: daily at 09:00 (system timezone)"
    echo "📝 Logs:     $LOG_DIR/"
    echo ""
    info "Run '$0 run' to kickstart immediately for testing."
    info "Run '$0 health' to verify everything is working."
}

cmd_uninstall() {
    echo "── Uninstalling AI Company OS launchd job ──"

    if [ ! -f "$PLIST_DEST" ]; then
        warn "Plist not found at $PLIST_DEST — nothing to uninstall."
        exit 0
    fi

    launchctl unload "$PLIST_DEST"
    ok "Launchd job unloaded: $LABEL"

    rm -f "$PLIST_DEST"
    ok "Plist removed from $PLIST_DEST"
}

cmd_status() {
    echo "── Launchd Job Status ──"
    echo ""

    # Check if plist exists
    if [ ! -f "$PLIST_DEST" ]; then
        fail "Plist not installed."
        echo "  Run '$0 install' first."
        exit 1
    fi

    # launchctl list output (macOS dict format on newer versions)
    local list_out
    list_out=$(launchctl list "$LABEL" 2>&1 || true)

    # Format 1: traditional table "PID\tExit\tLabel"
    if echo "$list_out" | grep -qE "^[0-9\-]+\s+[0-9\-]+\s+$LABEL"; then
        local pid exit_code
        read -r pid exit_code _ <<< "$list_out"
        if [ "$pid" = "-" ]; then
            if [ "$exit_code" = "0" ]; then
                ok "Job loaded. Last exit: 0 (success)"
            elif [ "$exit_code" = "-" ]; then
                ok "Job loaded. Last exit: still running or never exited"
            else
                fail "Job loaded. Last exit code: $exit_code"
            fi
        else
            ok "Job is running (PID: $pid)"
        fi
    # Format 2: dict format (macOS 14+)
    elif echo "$list_out" | grep -q '"Label"'; then
        local last_exit
        last_exit=$(echo "$list_out" | grep "LastExitStatus" | grep -oE '[0-9]+' || echo "-")
        if [ "$last_exit" = "0" ]; then
            ok "Job loaded. Last exit: 0 (success)"
        else
            ok "Job loaded. Last exit code: $last_exit"
        fi
    else
        fail "Job not found by launchctl."
        echo "  Output: $list_out"
        echo "  Try '$0 install' first."
        exit 1
    fi

    echo ""
    echo "📝 Log files:"
    if [ -f "$LOG_OUT" ]; then
        local out_size
        out_size=$(wc -c < "$LOG_OUT" | tr -d ' ')
        local out_lines
        out_lines=$(wc -l < "$LOG_OUT" | tr -d ' ')
        ok "stdout: $LOG_OUT ($out_lines lines, ${out_size}B)"
    else
        warn "stdout log: not yet created"
    fi
    if [ -f "$LOG_ERR" ]; then
        local err_size
        err_size=$(wc -c < "$LOG_ERR" | tr -d ' ')
        local err_lines
        err_lines=$(wc -l < "$LOG_ERR" | tr -d ' ')
        ok "stderr: $LOG_ERR ($err_lines lines, ${err_size}B)"
    else
        warn "stderr log: not yet created"
    fi

    # Show last WO from DB
    if [ -f "$DATABASE_PATH" ]; then
        echo ""
        echo "📊 Last Work Order in DB:"
        python3 -c "
import sqlite3, sys
try:
    conn = sqlite3.connect('$DATABASE_PATH')
    cur = conn.execute('SELECT work_order_id, skill_id, status, created_at FROM work_orders ORDER BY created_at DESC LIMIT 1')
    row = cur.fetchone()
    if row:
        print(f'  ID:       {row[0]}')
        print(f'  Skill:    {row[1]}')
        print(f'  Status:   {row[2]}')
        print(f'  Created:  {row[3]}')
    else:
        print('  (no work orders found)')
    conn.close()
except Exception as e:
    print(f'  (DB query failed: {e})')
" 2>/dev/null || warn "Could not query DB"
    else
        warn "Database file not found at: $DATABASE_PATH"
    fi
}

cmd_run() {
    echo "── Kickstarting launchd job ──"
    echo ""

    if [ ! -f "$PLIST_DEST" ]; then
        fail "Plist not installed. Run '$0 install' first."
        exit 1
    fi

    # Ensure log dir exists
    mkdir -p "$LOG_DIR"

    info "Triggering: launchctl kickstart gui/501/$LABEL"
    launchctl kickstart -p "gui/501/$LABEL" 2>&1 || {
        # Fallback for older macOS versions
        launchctl start "$LABEL" 2>&1
    }

    echo ""
    info "Job triggered. Run '$0 logs' to monitor output."
    info "Run '$0 health' after ~2 minutes to check results."
}

cmd_logs() {
    echo "── Recent Logs ──"
    echo ""

    if [ -f "$LOG_OUT" ]; then
        echo "=== stdout (last 30 lines) ==="
        tail -30 "$LOG_OUT"
    else
        warn "stdout log not yet created."
    fi

    echo ""

    if [ -f "$LOG_ERR" ]; then
        local err_size
        err_size=$(wc -c < "$LOG_ERR" | tr -d ' ')
        echo "=== stderr (last 30 lines, ${err_size}B) ==="
        tail -30 "$LOG_ERR"
    else
        warn "stderr log not yet created."
    fi
}

cmd_health() {
    echo "══ AI Company OS — Launchd Health Check ══"
    echo ""

    local all_ok=true

    # 1. Plist installed?
    if [ -f "$PLIST_DEST" ]; then
        ok "Plist installed at $PLIST_DEST"
    else
        fail "Plist NOT installed. Run '$0 install' first."
        all_ok=false
    fi

    # 2. Job loaded in launchd?
    if launchctl list "$LABEL" &>/dev/null; then
        local list_out
        list_out=$(launchctl list "$LABEL" 2>&1)
        # Format 1: traditional table
        if echo "$list_out" | grep -qE "^[0-9\-]+\s+[0-9\-]+\s+$LABEL"; then
            local exit_code
            read -r _ exit_code _ <<< "$list_out"
            if [ "$exit_code" = "0" ]; then
                ok "Job loaded, last exit: 0 (success)"
            elif [ "$exit_code" = "-" ]; then
                ok "Job loaded (no exit history yet)"
            else
                warn "Job loaded but last exit code: $exit_code"
            fi
        # Format 2: dict format
        elif echo "$list_out" | grep -q '"Label"'; then
            local last_exit
            last_exit=$(echo "$list_out" | grep "LastExitStatus" | grep -oE '[0-9]+' || echo "-")
            case "$last_exit" in
                0) ok "Job loaded, last exit: 0 (success)" ;;
                -) ok "Job loaded (no exit history yet)" ;;
                *) warn "Job loaded but last exit code: $last_exit" ;;
            esac
        else
            warn "Job loaded but unrecognized format: $list_out"
        fi
    else
        fail "Job NOT loaded in launchd"
        all_ok=false
    fi

    # 3. Log files — check for errors
    if [ -f "$LOG_ERR" ]; then
        local err_size
        err_size=$(wc -c < "$LOG_ERR" | tr -d ' ')
        if [ "$err_size" -gt 0 ]; then
            local err_errors
            err_errors=$(grep -ci "error\|traceback\|exception" "$LOG_ERR" 2>/dev/null || echo 0)
            if [ "$err_errors" -gt 0 ]; then
                warn "stderr log has $err_errors ERROR/Traceback entries ($err_size bytes)"
                all_ok=false
            else
                ok "stderr log exists ($err_size bytes, no errors)"
            fi
        else
            warn "stderr log is empty"
        fi
    fi
    if [ -f "$LOG_OUT" ]; then
        local out_size
        out_size=$(wc -c < "$LOG_OUT" | tr -d ' ')
        ok "stdout log exists ($out_size bytes)"
    else
        warn "stdout log not yet created"
    fi

    # 4. DB exists + last WO status
    if [ -f "$DATABASE_PATH" ]; then
        ok "Database exists at: $DATABASE_PATH"
        local db_result
        db_result=$(python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DATABASE_PATH')
    cur = conn.execute('''
        SELECT status, COUNT(*) as cnt
        FROM work_orders
        WHERE DATE(created_at) = DATE('now', 'localtime')
        GROUP BY status
        ORDER BY cnt DESC
    ')
    rows = cur.fetchall()
    if rows:
        for status, cnt in rows:
            icon = '✅' if status == 'completed' else ('🟡' if status in ('pending','dispatched') else '🔴')
            print(f'  {icon} {status}: {cnt}')
    else:
        print('  ℹ️  No work orders today yet')
        # Show latest from any day
        cur2 = conn.execute('SELECT work_order_id, skill_id, status, created_at FROM work_orders ORDER BY created_at DESC LIMIT 1')
        row2 = cur2.fetchone()
        if row2:
            print(f'  Latest: {row2[0]} — {row2[1]} — {row2[2]} — {row2[3]}')
    conn.close()
except Exception as e:
    print(f'  Error: {e}')
" 2>&1)
        echo "$db_result"
    else
        fail "Database NOT found at: $DATABASE_PATH"
        all_ok=false
    fi

    echo ""
    if [ "$all_ok" = true ]; then
        ok "All checks passed ✅"
    else
        warn "Some checks failed — review above."
    fi
}

# ── Main ──────────────────────────────────────────────────────────────
case "${1:-help}" in
    install)   cmd_install ;;
    uninstall) cmd_uninstall ;;
    status)    cmd_status ;;
    run)       cmd_run ;;
    logs)      cmd_logs ;;
    health)    cmd_health ;;
    *)         usage ;;
esac
