export default function ConfirmModal({ isOpen, title, message, onConfirm, onCancel }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-sm w-full mx-4">
        <h3 className="text-white font-semibold text-lg">{title}</h3>
        <p className="text-slate-400 text-sm mt-2">{message}</p>
        <div className="flex gap-3 mt-6 justify-end">
          <button onClick={onCancel} className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors">
            Cancel
          </button>
          <button onClick={onConfirm} className="px-4 py-2 text-sm bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors">
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
