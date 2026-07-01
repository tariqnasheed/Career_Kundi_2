/**
 * ChatbotPage.tsx
 * ================
 * Full-page career assistant chat — session history sidebar + main conversation.
 * Mirrors the ChatbotWidget but with a full layout, citation display,
 * memory browser, and session management.
 */

import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare, Plus, Trash2, Send, Loader2,
  Brain, Link, ChevronRight, Bot, User,
} from "lucide-react";
import { chatbotApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";
import type { ChatSessionRead, ChatMessageRead } from "../types/api";

// ─── Message bubble ────────────────────────────────────────────────────────
function MessageBubble({ msg }: { msg: ChatMessageRead & { isOptimistic?: boolean } }) {
  const isUser = msg.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: "flex",
        flexDirection: isUser ? "row-reverse" : "row",
        gap: "0.625rem",
        marginBottom: "1rem",
        alignItems: "flex-start",
      }}
    >
      {/* Avatar */}
      <div style={{
        width: "28px", height: "28px", borderRadius: "50%", flexShrink: 0,
        background: isUser ? "var(--accent-violet)" : "var(--gradient-primary)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        {isUser ? <User size={13} color="#fff" /> : <Bot size={13} color="#fff" />}
      </div>

      <div style={{ maxWidth: "70%" }}>
        {/* Content */}
        <div style={{
          padding: "0.75rem 1rem",
          borderRadius: isUser ? "18px 18px 4px 18px" : "4px 18px 18px 18px",
          background: isUser ? "var(--accent-violet)" : "var(--bg-glass)",
          backdropFilter: "blur(16px)",
          border: isUser ? "none" : "1px solid var(--border-subtle)",
          color: isUser ? "#fff" : "var(--text-primary)",
          fontSize: "0.875rem",
          lineHeight: 1.65,
          opacity: msg.isOptimistic ? 0.7 : 1,
        }}>
          {msg.content}
        </div>

        {/* Citations */}
        {msg.citations && msg.citations.length > 0 && (
          <div style={{ marginTop: "0.4rem", display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
            {msg.citations.map((c: any, i: number) => (
              <a
                key={i}
                href={c.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-flex", alignItems: "center", gap: "4px",
                  padding: "2px 8px", borderRadius: "4px",
                  background: "rgba(139,92,246,0.08)",
                  color: "var(--accent-violet)", fontSize: "0.7rem",
                  textDecoration: "none", border: "1px solid rgba(139,92,246,0.2)",
                }}
              >
                <Link size={9} />{c.title ?? `Source ${i + 1}`}
              </a>
            ))}
          </div>
        )}

        {/* Confidence */}
        {msg.confidence_score != null && (
          <p style={{ fontSize: "0.65rem", color: "var(--text-secondary)", marginTop: "3px" }}>
            Confidence: {Math.round(msg.confidence_score * 100)}%
          </p>
        )}
      </div>
    </motion.div>
  );
}

// ─── Thinking indicator ────────────────────────────────────────────────────
function ThinkingBubble() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: "flex", gap: "0.625rem", marginBottom: "1rem" }}>
      <div style={{ width: "28px", height: "28px", borderRadius: "50%", background: "var(--gradient-primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Bot size={13} color="#fff" />
      </div>
      <div style={{
        padding: "0.75rem 1rem", borderRadius: "4px 18px 18px 18px",
        background: "var(--bg-glass)", backdropFilter: "blur(16px)",
        border: "1px solid var(--border-subtle)",
        display: "flex", gap: "5px", alignItems: "center",
      }}>
        {[0, 1, 2].map(i => (
          <motion.div key={i}
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
            style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--accent-violet)" }}
          />
        ))}
      </div>
    </motion.div>
  );
}

// ─── Follow-up chips ───────────────────────────────────────────────────────
const FOLLOW_UPS = [
  "Help me prepare for a behavioural interview",
  "Review my CV for this role",
  "What skills should I prioritise?",
  "How do I negotiate my salary?",
];

// ─── Session list item ─────────────────────────────────────────────────────
function SessionItem({ session, active, onClick, onDelete }: {
  session: ChatSessionRead; active: boolean;
  onClick: () => void; onDelete: () => void;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        display: "flex", alignItems: "center", gap: "0.5rem",
        padding: "0.6rem 0.875rem", borderRadius: "10px",
        background: active ? "rgba(139,92,246,0.1)" : "transparent",
        border: active ? "1px solid rgba(139,92,246,0.3)" : "1px solid transparent",
        cursor: "pointer", transition: "all 0.15s",
      }}
    >
      <MessageSquare size={13} style={{ color: active ? "var(--accent-violet)" : "var(--text-secondary)", flexShrink: 0 }} />
      <span style={{ flex: 1, fontSize: "0.8rem", fontWeight: active ? 600 : 400, color: active ? "var(--text-primary)" : "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {session.title || "New chat"}
      </span>
      <button
        onClick={e => { e.stopPropagation(); onDelete(); }}
        style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", opacity: 0, padding: "2px" }}
        className="delete-btn"
      >
        <Trash2 size={12} />
      </button>
    </div>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────
export default function ChatbotPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [localMessages, setLocalMessages] = useState<(ChatMessageRead & { isOptimistic?: boolean })[]>([]);

  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: () => chatbotApi.listSessions(),
  });

  const { data: activeSession } = useQuery({
    queryKey: ["chat-session", activeSessionId],
    queryFn: () => chatbotApi.getSession(activeSessionId!),
    enabled: !!activeSessionId,
  });

  // Sync fetched session messages into local state (react-query v5: no onSuccess in useQuery)
  useEffect(() => {
    if (activeSession) setLocalMessages((activeSession as any).messages ?? []);
  }, [activeSession?.id]);

  const createSession = useMutation({
    mutationFn: () => chatbotApi.createSession(),
    onSuccess: (session: ChatSessionRead) => {
      qc.invalidateQueries({ queryKey: ["chat-sessions"] });
      setActiveSessionId(session.id);
      setLocalMessages([]);
    },
  });

  const deleteSession = useMutation({
    mutationFn: (id: string) => chatbotApi.deleteSession(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["chat-sessions"] });
      if (activeSessionId === id) { setActiveSessionId(null); setLocalMessages([]); }
    },
  });

  const sendMutation = useMutation({
    mutationFn: ({ sessionId, content }: { sessionId: string; content: string }) =>
      chatbotApi.sendMessage(sessionId, content),
    onSuccess: (turn: any) => {
      setThinking(false);
      setLocalMessages(prev => {
        const withoutOptimistic = prev.filter(m => !m.isOptimistic);
        return [...withoutOptimistic, turn.user_message, turn.assistant_message];
      });
      qc.invalidateQueries({ queryKey: ["chat-session", activeSessionId] });
    },
    onError: () => {
      setThinking(false);
      setLocalMessages(prev => prev.filter(m => !m.isOptimistic));
      addToast({ type: "error", message: "Message failed. Try again." });
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [localMessages, thinking]);

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content) return;

    let sessionId = activeSessionId;
    if (!sessionId) {
      const s = await createSession.mutateAsync();
      sessionId = s.id;
    }

    setInput("");
    setThinking(true);
    setLocalMessages(prev => [
      ...prev,
      { id: "optimistic", role: "user", content, session_id: sessionId!, created_at: new Date().toISOString(), isOptimistic: true } as any,
    ]);
    sendMutation.mutate({ sessionId: sessionId!, content });
  };

  const { data: memory } = useQuery({
    queryKey: ["chat-memory"],
    queryFn: () => chatbotApi.listMemory(),
  });

  const messages = activeSessionId ? localMessages : [];

  return (
    <div style={{ display: "flex", height: "calc(100vh - 56px)", overflow: "hidden" }}>
      {/* ── Session sidebar ── */}
      <div style={{
        width: "260px", flexShrink: 0,
        borderRight: "1px solid var(--border-subtle)",
        background: "var(--bg-base)",
        display: "flex", flexDirection: "column",
      }}>
        <div style={{ padding: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
          <Button
            variant="secondary"
            size="sm"
            fullWidth
            leftIcon={<Plus size={14} />}
            onClick={() => createSession.mutate()}
            loading={createSession.isPending}
          >
            New conversation
          </Button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "0.75rem" }}>
          {sessionsLoading && <div style={{ textAlign: "center", padding: "1rem" }}><Spinner size="sm" /></div>}
          {sessions?.map((s: ChatSessionRead) => (
            <SessionItem
              key={s.id}
              session={s}
              active={s.id === activeSessionId}
              onClick={() => setActiveSessionId(s.id)}
              onDelete={() => deleteSession.mutate(s.id)}
            />
          ))}
          {!sessionsLoading && !sessions?.length && (
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textAlign: "center", padding: "1rem" }}>
              No conversations yet.
            </p>
          )}
        </div>

        {/* Memory count */}
        {(memory?.length ?? 0) > 0 && (
          <div style={{ padding: "0.75rem", borderTop: "1px solid var(--border-subtle)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem", borderRadius: "8px", background: "rgba(139,92,246,0.08)" }}>
              <Brain size={12} style={{ color: "var(--accent-violet)" }} />
              <span style={{ fontSize: "0.72rem", color: "var(--text-secondary)" }}>{memory?.length ?? 0} memories stored</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Chat area ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--bg-base)" }}>
        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem 2rem" }}>
          {!activeSessionId && !createSession.isPending && (
            <div style={{ textAlign: "center", paddingTop: "6rem", color: "var(--text-secondary)" }}>
              <Bot size={48} style={{ margin: "0 auto 1rem", opacity: 0.3 }} />
              <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 700, marginBottom: "0.5rem" }}>Career AI assistant</h2>
              <p style={{ fontSize: "0.875rem", marginBottom: "2rem" }}>Ask me anything about your career, job search, CV, or interview prep.</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", justifyContent: "center" }}>
                {FOLLOW_UPS.map(q => (
                  <button key={q} onClick={() => handleSend(q)} style={{
                    padding: "0.5rem 0.875rem", borderRadius: "999px",
                    border: "1px solid var(--border-subtle)", background: "var(--bg-overlay)",
                    color: "var(--text-secondary)", cursor: "pointer", fontSize: "0.8rem",
                  }}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
          {thinking && <ThinkingBubble />}
          <div ref={messagesEndRef} />
        </div>

        {/* Follow-up chips (when session active) */}
        {activeSessionId && messages.length > 0 && !thinking && (
          <div style={{ padding: "0 2rem 0.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {FOLLOW_UPS.slice(0, 2).map(q => (
              <button key={q} onClick={() => handleSend(q)} style={{
                padding: "0.375rem 0.75rem", borderRadius: "999px",
                border: "1px solid rgba(139,92,246,0.3)", background: "rgba(139,92,246,0.05)",
                color: "var(--accent-violet)", cursor: "pointer", fontSize: "0.75rem",
              }}>
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input bar */}
        <div style={{
          padding: "0.875rem 2rem 1.25rem",
          borderTop: "1px solid var(--border-subtle)",
          background: "var(--bg-glass)", backdropFilter: "blur(16px)",
        }}>
          <div style={{
            display: "flex", gap: "0.75rem", alignItems: "flex-end",
            padding: "0.625rem 0.875rem", borderRadius: "16px",
            background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)",
          }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask your career AI assistant…"
              rows={1}
              style={{
                flex: 1, background: "none", border: "none", outline: "none",
                color: "var(--text-primary)", fontSize: "0.875rem",
                resize: "none", lineHeight: 1.5, maxHeight: "120px", overflowY: "auto",
                fontFamily: "var(--font-sans)",
              }}
            />
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleSend()}
              loading={thinking}
              disabled={!input.trim() && !thinking}
              style={{ borderRadius: "10px", flexShrink: 0 }}
            >
              <Send size={14} />
            </Button>
          </div>
          <p style={{ fontSize: "0.67rem", color: "var(--text-secondary)", textAlign: "center", marginTop: "0.4rem" }}>
            AI may make mistakes. Always verify important career decisions.
          </p>
        </div>
      </div>
    </div>
  );
}
