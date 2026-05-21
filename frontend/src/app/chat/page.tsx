'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import {
  sendChatMessage,
  getChatSessions,
  getChatSession,
  deleteChatSession,
} from '@/lib/api'
import type { ChatSessionItem, ChatMessage } from '@/types/api'

// ── Helpers ──

function dateGroup(dateStr: string | null): string {
  if (!dateStr) return '未知'
  const d = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays}天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function formatTime(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// ── Markdown renderer (lightweight) ──

function Markdown({ content }: { content: string }) {
  // Simple markdown-like rendering (no full parser needed for Hermes output)
  const html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // code blocks (```...```)
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
      const langLabel = lang ? `<span class="text-xs text-zinc-500 mb-1 block">${lang}</span>` : ''
      return `<pre class="bg-zinc-900 border border-zinc-700 rounded-lg p-3 my-2 overflow-x-auto text-sm"><code>${langLabel}${code.trim()}</code></pre>`
    })
    // inline code
    .replace(/`([^`]+)`/g, '<code class="bg-zinc-800 px-1 py-0.5 rounded text-sm text-orange-300">$1</code>')
    // bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold">$1</strong>')
    // italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // horizontal rule
    .replace(/^---+/gm, '<hr class="my-3 border-zinc-700" />')
    // blockquote
    .replace(/^>\s?(.+)$/gm, '<blockquote class="border-l-2 border-blue-500 pl-3 my-2 text-zinc-400">$1</blockquote>')
    // bullet lists
    .replace(/^[-*]\s(.+)$/gm, '<li class="ml-4 list-disc text-zinc-200">$1</li>')
    // numbered lists
    .replace(/^\d+\.\s(.+)$/gm, '<li class="ml-4 list-decimal text-zinc-200">$1</li>')
    // line breaks (double for paragraphs)
    .replace(/\n\n/g, '</p><p class="mb-2">')
    // single line breaks
    .replace(/\n/g, '<br />')

  return (
    <div
      className="prose-sm max-w-none leading-relaxed"
      dangerouslySetInnerHTML={{ __html: `<p class="mb-2">${html}</p>` }}
    />
  )
}

// ── Message Bubble ──

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600/90 text-white rounded-br-md'
            : 'bg-zinc-800/80 text-zinc-200 border border-zinc-700/50 rounded-bl-md'
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
        ) : (
          <>
            <div className="flex items-center gap-2 mb-1.5 text-xs text-zinc-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Hermes Agent
              {msg.metadata && (() => {
                try {
                  const meta = JSON.parse(msg.metadata)
                  return meta.tokens_used ? <span>· {meta.tokens_used} tokens</span> : null
                } catch { return null }
              })()}
            </div>
            <Markdown content={msg.content} />
          </>
        )}
        <div className={`text-[10px] mt-1 ${isUser ? 'text-blue-200/60 text-right' : 'text-zinc-600'}`}>
          {formatTime(msg.created_at)}
        </div>
      </div>
    </div>
  )
}

// ── Main Chat Page ──

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSessionItem[]>([])
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Scroll to bottom on new messages
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  async function loadSessions() {
    setLoadingSessions(true)
    try {
      const data = await getChatSessions(50)
      setSessions(data)
    } catch (e) {
      console.error('Failed to load sessions', e)
    } finally {
      setLoadingSessions(false)
    }
  }

  async function loadSessionMessages(sessionId: number) {
    setLoadingMessages(true)
    setError(null)
    try {
      const data = await getChatSession(sessionId)
      setMessages(data.messages)
    } catch (e) {
      setError('加载会话失败')
      console.error(e)
    } finally {
      setLoadingMessages(false)
    }
  }

  function selectSession(sessionId: number) {
    setActiveSessionId(sessionId)
    loadSessionMessages(sessionId)
  }

  async function handleSend() {
    const text = input.trim()
    if (!text || sending) return

    setSending(true)
    setError(null)

    // Optimistic user message
    const optimisticMsg: ChatMessage = {
      id: -Date.now(),
      role: 'user',
      content: text,
      metadata: null,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimisticMsg])
    setInput('')

    try {
      const res = await sendChatMessage({
        message: text,
        session_id: activeSessionId,
      })

      // Add assistant reply
      const assistantMsg: ChatMessage = {
        id: -Date.now() - 1,
        role: 'assistant',
        content: res.reply,
        metadata: res.tokens_used ? JSON.stringify({ tokens_used: res.tokens_used }) : null,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])

      // If new session, update activeSessionId and reload sessions
      if (!activeSessionId || res.session_id !== activeSessionId) {
        setActiveSessionId(res.session_id)
        loadSessions()
      } else {
        // Just refresh the session list to update titles/message counts
        loadSessions()
      }
    } catch (e) {
      setError('发送失败，请重试')
      console.error(e)
    } finally {
      setSending(false)
    }
  }

  async function handleDelete(sessionId: number) {
    if (!confirm('删除此对话？')) return
    try {
      await deleteChatSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (activeSessionId === sessionId) {
        setActiveSessionId(null)
        setMessages([])
      }
    } catch (e) {
      console.error(e)
    }
  }

  function handleNewSession() {
    setActiveSessionId(null)
    setMessages([])
    setError(null)
    setInput('')
    inputRef.current?.focus()
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Filtered sessions
  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Group sessions by date
  const groupedSessions: Record<string, ChatSessionItem[]> = {}
  filteredSessions.forEach((s) => {
    const group = dateGroup(s.updated_at)
    if (!groupedSessions[group]) groupedSessions[group] = []
    groupedSessions[group].push(s)
  })

  return (
    <div className="flex h-[calc(100vh-7rem)] -mx-4 gap-0">
      {/* ── Sidebar ── */}
      <div className="w-64 flex-shrink-0 border-r border-zinc-800 flex flex-col bg-zinc-900/50">
        {/* New Session Button */}
        <div className="p-3 border-b border-zinc-800">
          <button
            onClick={handleNewSession}
            className={`w-full py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
              activeSessionId === null
                ? 'bg-blue-600 text-white'
                : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700 border border-zinc-700'
            }`}
          >
            + 新建对话
          </button>
        </div>

        {/* Search */}
        <div className="px-3 py-2">
          <input
            type="text"
            placeholder="搜索对话..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-zinc-300 placeholder-zinc-500 focus:outline-none focus:border-blue-500/50"
          />
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {loadingSessions ? (
            <div className="flex items-center justify-center h-20 text-sm text-zinc-500">
              加载中...
            </div>
          ) : Object.keys(groupedSessions).length === 0 ? (
            <div className="flex items-center justify-center h-20 text-sm text-zinc-500">
              {searchQuery ? '无匹配对话' : '暂无对话'}
            </div>
          ) : (
            Object.entries(groupedSessions).map(([group, items]) => (
              <div key={group}>
                <div className="px-3 py-1.5 text-xs text-zinc-600 font-medium">{group}</div>
                {items.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => selectSession(s.id)}
                    className={`group flex items-center justify-between px-3 py-2 mx-1 rounded-lg cursor-pointer transition-colors ${
                      activeSessionId === s.id
                        ? 'bg-zinc-700/60 text-white'
                        : 'text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm truncate">{s.title}</div>
                      <div className="text-[11px] text-zinc-600 mt-0.5">
                        {s.message_count} 条消息
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(s.id)
                      }}
                      className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition-all p-1 text-xs"
                      title="删除"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Main Chat Area ── */}
      <div className="flex-1 flex flex-col bg-zinc-900/30">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-thin">
          {activeSessionId === null && messages.length === 0 ? (
            // Empty state — no active session
            <div className="flex flex-col items-center justify-center h-full text-zinc-500">
              <div className="text-4xl mb-4">💬</div>
              <h2 className="text-lg font-medium text-zinc-400 mb-2">对话面板</h2>
              <p className="text-sm text-zinc-600 text-center max-w-md mb-6">
                和 Hermes Agent 深度讨论 · 与飞书消息互联互通
              </p>
              <div className="text-xs text-zinc-700 space-y-1">
                <p>💡 在左侧选择一个已有对话，或点击「新建对话」开始新话题</p>
                <p>📱 手机端用飞书，桌面端用这里，消息互通</p>
              </div>
            </div>
          ) : loadingMessages ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-pulse text-zinc-500">加载对话...</div>
            </div>
          ) : messages.length === 0 ? (
            // Empty state — new session, no messages yet
            <div className="flex flex-col items-center justify-center h-full text-zinc-500">
              <div className="text-4xl mb-4">🔄</div>
              <p className="text-sm text-zinc-600">新对话</p>
              <p className="text-xs text-zinc-700 mt-1">输入消息开始和 Hermes 对话</p>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
              {sending && (
                <div className="flex justify-start mb-4">
                  <div className="bg-zinc-800/80 border border-zinc-700/50 rounded-2xl rounded-bl-md px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}

          {error && (
            <div className="text-center py-2">
              <span className="text-xs text-red-400 bg-red-500/10 px-3 py-1 rounded-full">
                {error}
              </span>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-zinc-800 p-4">
          <div className="flex items-end gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
              rows={1}
              disabled={sending}
              className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-500 resize-none focus:outline-none focus:border-blue-500/50 disabled:opacity-50 min-h-[44px] max-h-32"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sending}
              className="px-4 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-xl text-sm font-medium transition-colors disabled:cursor-not-allowed min-w-[80px]"
            >
              {sending ? '发送中' : '发送'}
            </button>
          </div>
          <div className="mt-1.5 text-[11px] text-zinc-700 text-center">
            Hermes Agent · DeepSeek V4 Flash · 桌面对话
          </div>
        </div>
      </div>
    </div>
  )
}
