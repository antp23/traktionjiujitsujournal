import { useCallback, useEffect, useState } from "react";
import { Inbox, Pin, Send, ShieldCheck } from "lucide-react";
import { createThreadMessage, getSharedInbox, pinThreadMessage } from "../lib/api";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";

function threadId(thread) {
  return thread.thread_id || thread.id;
}

function messageId(message) {
  return message.message_id || message.id;
}

function threadMessages(thread) {
  return thread.messages || thread.thread_messages || [];
}

export default function SharedInbox() {
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [drafts, setDrafts] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getSharedInbox();
      setThreads(Array.isArray(response.data) ? response.data : response.data.threads || []);
    } catch {
      setError("Could not load shared inbox.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const sendMessage = async (id) => {
    const body = (drafts[id] || "").trim();
    if (!body) return;

    try {
      await createThreadMessage(id, { body });
      setDrafts((current) => ({ ...current, [id]: "" }));
      load();
    } catch {
      setError("Could not send reply.");
    }
  };

  const pinMessage = async (id) => {
    try {
      await pinThreadMessage(id);
      load();
    } catch {
      setError("Could not pin that message.");
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-purple-700">Coach threads</p>
        <h1 className="text-2xl font-bold text-gray-950 mt-1">Shared Inbox</h1>
        <p className="text-sm text-gray-500 mt-1">This only shows items that were deliberately shared from Goals or Notes.</p>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}

      {threads.length === 0 ? (
        <EmptyState
          message="No shared threads yet. When an athlete uses Ask coach, the conversation appears here."
          icon={Inbox}
          action={(
            <div className="privacy-note inline-note">
              <ShieldCheck className="w-4 h-4" />
              <span>Private journal entries do not appear in this inbox.</span>
            </div>
          )}
        />
      ) : (
        <div className="space-y-3">
          {threads.map((thread) => {
            const id = threadId(thread);
            const messages = threadMessages(thread);

            return (
              <article key={id} className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 space-y-4">
                <div className="flex flex-wrap items-center gap-2 justify-between">
                  <div>
                    <h2 className="text-sm font-semibold text-gray-950">{thread.title || `${thread.source_type || "Shared item"} thread`}</h2>
                    <p className="text-xs text-gray-500">{thread.status || "open"} {thread.source_type ? `- shared ${thread.source_type}` : ""}</p>
                  </div>
                  {thread.source_id && <span className="text-xs text-gray-400">Source: {thread.source_id}</span>}
                </div>

                <div className="space-y-2">
                  {messages.map((message) => {
                    const id = messageId(message);
                    return (
                      <div key={id} className="bg-gray-50 border border-gray-100 rounded-lg p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm text-gray-800 whitespace-pre-wrap">{message.body}</p>
                            <p className="text-xs text-gray-400 mt-1">{message.author_name || message.author_email || message.author_role || "Member"}</p>
                          </div>
                          <button onClick={() => pinMessage(id)} className="p-1.5 rounded text-gray-400 hover:text-purple-700" title="Pin as coach note">
                            <Pin className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="flex gap-2">
                  <input
                    value={drafts[id] || ""}
                    onChange={(event) => setDrafts((current) => ({ ...current, [id]: event.target.value }))}
                    placeholder="Write a reply..."
                    className="flex-1 rounded-lg px-3 py-2 text-sm"
                  />
                  <button onClick={() => sendMessage(id)} className="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded-lg px-3 py-2">
                    <Send className="w-4 h-4" /> Reply
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
