/**
 * components/chatbot/ChatbotWidget.tsx
 * =====================================
 * Floating chatbot entry-point.
 *
 * Two-state UI:
 *   Collapsed  – FAB button (violet Sparkles icon) in the bottom-right
 *   Expanded   – glass panel that slides up from the FAB
 *
 * Architecture:
 *   – React Query mutation for POST /chatbot/sessions/:id/messages
 *   – Local state tracks messages for the current session
 *   – On first open, creates a new session (POST /chatbot/sessions)
 *   – Suggested follow-ups appear after each assistant turn
 *   – Citations render as numbered superscript links
 *   – Input disabled while mutation is pending
 *   – Escape key closes the panel
 *
 * Note: full streaming will be wired in Task #10; here we use
 * request/response but with an "AI thinking" intermediate state so the UX
 * feels live.
 */

import {
  useState, useRef, useEffect, useCallback, type KeyboardEvent,
} from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { Sparkles, X, Send, RefreshCw } from "lucide-react";
import { clsx } from "clsx";
import { chatbotApi } from "../../lib/api";
import type { ChatMessageRead, ChatTurnResponse, ChatSessionRead } from "../../types/api";
import { useUIStore } from "../../store/ui";
import { useAuthStore } from "../../store/auth";
import { Spinner } from "../ui/Spinner";
import styles from "./ChatbotWidget.module.css";

/* ── local types ─────────────────────────────────────────────────── */
interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  suggested_followups?: string[];
  citations?: { n: number; title: string; url: string }[];
}

/* ── helpers ─────────────────────────────────────────────────────── */
function toDisplay(msg: ChatMessageRead, followups?: string[]): DisplayMessage {
  return {
    id: msg.id,
    role: msg.role as "user" | "assistant",
    content: msg.content,
    suggested_followups: followups,
    citations: msg.citations as DisplayMessage["citations"],
  };
}

/* ── component ───────────────────────────────────────────────────── */
export function ChatbotWidget() {
  const { chatbotOpen, openChatbot, closeChatbot } = useUIStore();
  const { isAuthenticated } = useAuthStore();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  // Focus input when panel opens
  useEffect(() => {
    if (chatbotOpen) {
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [chatbotOpen]);

  // Escape to close
  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape" && chatbotOpen) closeChatbot();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [chatbotOpen, closeChatbot]);

  // --- Create session lazily on first open --------------------------
  const createSessionMutation = useMutation({
    mutationFn: () => chatbotApi.createSession("Quick chat"),
    onSuccess: (data: ChatSessionRead) => {
      setSessionId(data.id);
    },
  });

  useEffect(() => {
    if (chatbotOpen && isAuthenticated && !sessionId && !createSessionMutation.isPending) {
      createSessionMutation.mutate();
    }
  }, [chatbotOpen, isAuthenticated, sessionId]); // eslint-disable-line

  // --- Send message mutation ----------------------------------------
  const sendMutation = useMutation({
    mutationFn: (content: string) =>
      chatbotApi.sendMessage(sessionId!, content) as Promise<ChatTurnResponse>,
    onMutate: (content) => {
      // Optimistic user bubble
      const tempUserMsg: DisplayMessage = {
        id: `temp-${Date.now()}`,
        role: "user",
        content,
      };
      setMessages((prev) => [...prev, tempUserMsg]);
      setIsThinking(true);
    },
    onSuccess: (data: ChatTurnResponse) => {
      setIsThinking(false);
      setMessages((prev) => {
        // Replace temp user bubble with real one, append assistant
        const without = prev.filter((m) => !m.id.startsWith("temp-"));
        return [
          ...without,
          toDisplay(data.user_message),
          toDisplay(data.assistant_message, data.assistant_message.suggested_followups),
        ];
      });
    },
    onError: () => {
      setIsThinking(false);
      setMessages((prev) => prev.filter((m) => !m.id.startsWith("temp-")));
      useUIStore.getState().addToast({
        type: "error",
        title: "Couldn't send message",
        message: "Please try again.",
      });
    },
  });

  const handleSubmit = useCallback(
    (content: string) => {
      const text = content.trim();
      if (!text || !sessionId || sendMutation.isPending) return;
      setInput("");
      sendMutation.mutate(text);
    },
    [sessionId, sendMutation]
  );

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(input);
    }
  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
    createSessionMutation.mutate();
  };

  if (!isAuthenticated) return null;

  return (
    <>
      {/* ── FAB ──────────────────────────────────────────────────── */}
      <AnimatePresence>
        {!chatbotOpen && (
          <motion.button
            className={styles.fab}
            onClick={openChatbot}
            aria-label="Open AI assistant"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 22 }}
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.95 }}
          >
            <Sparkles size={22} />
          </motion.button>
        )}
      </AnimatePresence>

      {/* ── Panel ────────────────────────────────────────────────── */}
      <AnimatePresence>
        {chatbotOpen && (
          <motion.div
            className={styles.panel}
            role="dialog"
            aria-label="AI Career Assistant"
            aria-modal="false"
            initial={{ opacity: 0, y: 24, scale: 0.95 }}
            animate={{ opacity: 1, y: 0,  scale: 1 }}
            exit={{  opacity: 0, y: 24, scale: 0.95 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Header */}
            <div className={styles.panelHeader}>
              <div className={styles.panelTitle}>
                <span className={styles.panelIcon}><Sparkles size={14} /></span>
                <span>AI Career Assistant</span>
              </div>
              <div className={styles.panelActions}>
                <button
                  className={styles.headerBtn}
                  onClick={handleNewChat}
                  title="New conversation"
                  aria-label="New conversation"
                >
                  <RefreshCw size={14} />
                </button>
                <button
                  className={styles.headerBtn}
                  onClick={closeChatbot}
                  aria-label="Close assistant"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className={styles.messages} role="log" aria-live="polite">
              {messages.length === 0 && !isThinking && !createSessionMutation.isPending && (
                <div className={styles.empty}>
                  <span className={styles.emptyIcon}><Sparkles size={28} /></span>
                  <p className={styles.emptyTitle}>How can I help your career today?</p>
                  <p className={styles.emptyHint}>Ask me about jobs, interview prep, your CV, or career roadmap.</p>
                  <div className={styles.suggestions}>
                    {[
                      "What jobs match my profile?",
                      "Help me prepare for a React interview",
                      "Review my CV for improvements",
                      "What skills should I learn next?",
                    ].map((s) => (
                      <button
                        key={s}
                        className={styles.suggestionChip}
                        onClick={() => handleSubmit(s)}
                        disabled={!sessionId}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {(createSessionMutation.isPending) && (
                <div className={styles.centeredSpinner}>
                  <Spinner size="sm" />
                </div>
              )}

              {messages.map((msg) => (
                <div key={msg.id} className={clsx(styles.bubble, styles[msg.role])}>
                  <div className={styles.bubbleContent}>
                    {msg.content}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className={styles.citations}>
                        {msg.citations.map((c) => (
                          <a
                            key={c.n}
                            href={c.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.citation}
                            title={c.title}
                          >
                            [{c.n}]
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                  {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                    <div className={styles.followups}>
                      {msg.suggested_followups.map((f) => (
                        <button
                          key={f}
                          className={styles.followupChip}
                          onClick={() => handleSubmit(f)}
                          disabled={sendMutation.isPending}
                        >
                          {f}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* AI thinking state */}
              {isThinking && (
                <div className={clsx(styles.bubble, styles.assistant)}>
                  <div className={styles.bubbleContent}>
                    <Spinner variant="dots" size="sm" label="AI is thinking…" />
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className={styles.inputArea}>
              <textarea
                ref={inputRef}
                className={styles.input}
                placeholder="Ask anything about your career…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={sendMutation.isPending || !sessionId}
                aria-label="Message to AI assistant"
              />
              <button
                className={styles.sendBtn}
                onClick={() => handleSubmit(input)}
                disabled={!input.trim() || sendMutation.isPending || !sessionId}
                aria-label="Send message"
              >
                {sendMutation.isPending ? <Spinner size="sm" label="" /> : <Send size={16} />}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
