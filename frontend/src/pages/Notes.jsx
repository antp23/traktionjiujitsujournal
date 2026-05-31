import { useCallback, useEffect, useState } from "react";
import { getNotes, createNote, updateNote, deleteNote, createShareThread } from "../api";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import ConfirmModal from "../components/ConfirmModal";
import { Plus, Search, StickyNote, Trash2, Edit, MessageSquare } from "lucide-react";
import { format } from "date-fns";

function noteId(note) {
  return note.note_id || note.id;
}

export default function Notes() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(null);  // note being edited, or "new"
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [sharingId, setSharingId] = useState(null);
  const [shareBody, setShareBody] = useState("Can you look at this?");
  const [shareError, setShareError] = useState("");
  const [form, setForm] = useState({ title: "", content: "", tags: [] });
  const [tagInput, setTagInput] = useState("");

  const load = useCallback(() => {
    const params = {};
    if (search) params.search = search;
    getNotes(params).then(r => setNotes(r.data)).finally(() => setLoading(false));
  }, [search]);

  useEffect(() => { load(); }, [load]);

  const openNew = () => { setForm({ title: "", content: "", tags: [] }); setEditing("new"); };
  const openEdit = (note) => {
    setForm({ title: note.title || "", content: note.content, tags: note.tags || [] });
    setEditing(note.note_id);
  };

  const addTag = () => {
    if (tagInput.trim() && !form.tags.includes(tagInput.trim())) {
      setForm(f => ({ ...f, tags: [...f.tags, tagInput.trim()] }));
      setTagInput("");
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    if (editing === "new") {
      await createNote(form);
    } else {
      await updateNote(editing, form);
    }
    setEditing(null);
    load();
  };

  const handleDelete = async () => {
    await deleteNote(deleteTarget);
    setDeleteTarget(null);
    load();
  };

  const shareNote = async (note) => {
    setShareError("");
    try {
      await createShareThread({
        source_type: "note",
        source_id: noteId(note),
        body: shareBody.trim() || "Can you look at this?",
      });
      setSharingId(null);
      setShareBody("Can you look at this?");
    } catch {
      setShareError("Could not share this note with coach.");
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <ConfirmModal isOpen={Boolean(deleteTarget)} title="Delete Note" message="Permanently delete this note?"
        onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)} />

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notes</h1>
          <p className="text-sm text-gray-500 mt-1">Notes are private by default. Use Ask coach only when you want to start a shared thread.</p>
        </div>
        <button onClick={openNew} className="flex items-center gap-1.5 bg-purple-700 hover:bg-purple-600 text-white text-sm px-3 py-2 rounded-lg">
          <Plus className="w-4 h-4" /> New Note
        </button>
      </div>

      {shareError && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{shareError}</p>}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-2 w-4 h-4 text-gray-500" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search notes..."
          className="w-full bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg pl-9 pr-3 py-2" />
      </div>

      {/* Edit form */}
      {editing && (
        <form onSubmit={submit} className="bg-gray-50/60 border border-purple-700/30 rounded-xl p-4 space-y-3">
          <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Title (optional)" />
          <textarea required value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} rows={5}
            className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm resize-none"
            placeholder="Notes, concepts, YouTube rabbit holes..." />
          <div className="flex gap-2">
            <input value={tagInput} onChange={e => setTagInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addTag())}
              className="flex-1 bg-white border border-gray-200 text-gray-800 rounded px-2 py-1.5 text-sm" placeholder="Add tag..." />
            <button type="button" onClick={addTag} className="bg-slate-600 text-white px-2 rounded text-sm">+</button>
          </div>
          {form.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {form.tags.map(t => (
                <span key={t} className="flex items-center gap-1 bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full">
                  #{t} <button type="button" onClick={() => setForm(f => ({ ...f, tags: f.tags.filter(x => x !== t) }))} className="text-gray-500">x</button>
                </span>
              ))}
            </div>
          )}
          <div className="flex gap-3">
            <button type="submit" className="bg-purple-700 hover:bg-purple-600 text-white px-4 py-1.5 rounded-lg text-sm">Save</button>
            <button type="button" onClick={() => setEditing(null)} className="text-gray-500 hover:text-white text-sm px-3">Cancel</button>
          </div>
        </form>
      )}

      {/* Notes list */}
      {notes.length === 0 ? (
        <EmptyState message="No notes yet. Brain dump freely, then share only the notes that need coach eyes." icon={StickyNote}
          action={<button onClick={openNew} className="text-purple-400 text-sm">Write your first note &rarr;</button>} />
      ) : (
        <div className="space-y-2">
          {notes.map(note => (
            <div key={noteId(note)} className="bg-gray-50/60 border border-gray-100 rounded-xl p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {note.title && <h3 className="text-gray-900 font-semibold text-sm mb-1">{note.title}</h3>}
                  <p className="text-gray-700 text-sm whitespace-pre-wrap line-clamp-3">{note.content}</p>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="text-gray-400 text-xs">{format(new Date(note.created_at), "MMM d, yyyy")}</span>
                    {note.tags?.map(t => <span key={t} className="text-xs text-gray-400">#{t}</span>)}
                  </div>
                  {sharingId === noteId(note) ? (
                    <div className="mt-3 bg-white border border-gray-200 rounded-lg p-3 space-y-2">
                      <p className="text-xs text-gray-500">This sends the note and your message to Coach Inbox.</p>
                      <textarea value={shareBody} onChange={e => setShareBody(e.target.value)} rows={2}
                        className="w-full rounded-lg px-3 py-2 text-sm resize-none" />
                      <div className="flex gap-2">
                        <button onClick={() => shareNote(note)} className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-lg px-3 py-1.5">Send to coach</button>
                        <button onClick={() => setSharingId(null)} className="text-xs text-gray-500 px-2">Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <button onClick={() => setSharingId(noteId(note))} className="mt-3 inline-flex items-center gap-1.5 text-sm text-purple-700 hover:text-purple-600 font-medium">
                      <MessageSquare className="w-4 h-4" /> Ask coach
                    </button>
                  )}
                </div>
                <div className="flex gap-1 ml-3">
                  <button onClick={() => openEdit(note)} className="p-1.5 text-gray-500 hover:text-white rounded">
                    <Edit className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => setDeleteTarget(noteId(note))} className="p-1.5 text-gray-500 hover:text-red-400 rounded">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
