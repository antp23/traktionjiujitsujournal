import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, MessageSquare, ChevronDown, ChevronUp } from "lucide-react";
import { parseQuickLog } from "../api";

const HINTS = [
  "trained 1hr no gi, worked guard passing",
  "just got back from class, felt great",
  "note: remember to drill kimura from top half",
  "learned a calf slicer from 50/50 tonight",
  "1 hour gi yesterday, focused on takedowns",
];

export default function ChatInput({ onLogged }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [expanded, setExpanded] = useState(true);
  const [hint, setHint] = useState(0);
  const inputRef = useRef(null);
  const feedRef = useRef(null);

  useEffect(() => {
    const t = setInterval(() => setHint(h => (h + 1) % HINTS.length), 4000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [messages]);

  async function handleSubmit(e) {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setMessages(m => [...m, { role: "user", text: trimmed, id: Date.now() }]);
    setText("");
    setLoading(true);

    try {
      const res = await parseQuickLog(trimmed);
      const d = res.data;
      setMessages(m => [...m, { role: "bot", text: d.message, success: d.success, action: d.action, id: Date.now() + 1 }]);
      if (d.success && onLogged) onLogged(d.action);
    } catch {
      setMessages(m => [...m, { role: "bot", text: "Couldn't reach the tracker. Is the backend running?", success: false, id: Date.now() + 1 }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
  }

  return (
    <div className="overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between pb-3 group"
      >
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-sm" style={{ background: "var(--red-soft)" }}>
            <MessageSquare className="w-3.5 h-3.5" style={{ color: "var(--red)" }} />
          </div>
          <span className="text-gray-900 font-semibold text-sm">Quick Log</span>
          <span className="text-xs text-gray-400 hidden sm:inline">type naturally to log sessions or techniques</span>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
          : <ChevronDown className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
        }
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {/* Message feed */}
            {messages.length > 0 && (
              <div ref={feedRef} className="mb-3 max-h-40 overflow-y-auto space-y-2 border p-3" style={{ borderColor: "var(--line)", background: "var(--paper-soft)" }}>
                <AnimatePresence initial={false}>
                  {messages.map(msg => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div className={`max-w-[85%] px-3 py-2 rounded-xl text-sm ${
                        msg.role === "user"
                          ? "text-white rounded-br-sm"
                          : msg.success === false
                          ? "bg-amber-50 text-amber-700 border border-amber-200 rounded-bl-sm"
                          : "bg-white text-gray-800 border border-gray-200 rounded-bl-sm shadow-sm"
                      }`} style={msg.role === "user" ? { background: "var(--red)" } : undefined}>
                        {msg.text}
                      </div>
                    </motion.div>
                  ))}
                  {loading && (
                    <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                      <div className="bg-white border border-gray-200 px-3 py-2 rounded-xl rounded-bl-sm shadow-sm">
                        <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Input row */}
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={text}
                onChange={e => setText(e.target.value)}
                onKeyDown={handleKey}
                placeholder={HINTS[hint]}
                disabled={loading}
                className="flex-1 px-4 py-2.5 text-sm disabled:opacity-50"
              />
              <motion.button
                type="submit"
                disabled={!text.trim() || loading}
                className="p-2.5 disabled:bg-gray-100 disabled:text-gray-300 text-white transition-colors flex-shrink-0"
                style={{ background: text.trim() && !loading ? "var(--red)" : undefined }}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </motion.button>
            </form>

            {/* Example chips */}
            {messages.length === 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {["trained 1hr gi", "note: work on X-guard", "learned armbar from guard"].map(ex => (
                  <button
                    key={ex}
                    onClick={() => { setText(ex); inputRef.current?.focus(); }}
                    className="text-xs px-2.5 py-1 transition-colors border"
                    style={{ background: "var(--paper-soft)", borderColor: "var(--line)", color: "var(--muted)" }}
                  >
                    {ex}
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
