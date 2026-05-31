import { useState } from "react";
import { Link } from "react-router-dom";
import { Building2, Copy, KeyRound } from "lucide-react";
import { bootstrapWorkspace } from "../api";

export default function SetupWorkspace() {
  const [form, setForm] = useState({
    gym_name: "",
    owner_email: "",
    owner_name: "",
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setResult(null);
    setBusy(true);

    try {
      const response = await bootstrapWorkspace({
        gym_name: form.gym_name.trim(),
        owner_email: form.owner_email.trim(),
        owner_name: form.owner_name.trim() || null,
      });
      setResult(response.data);
    } catch {
      setError("Could not create the workspace. The backend may already have a gym, or one of the fields needs attention.");
    } finally {
      setBusy(false);
    }
  };

  const inviteCode = result?.invite?.code || "";
  const invitePath = inviteCode ? `/join/${inviteCode}` : "";

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 flex items-center justify-center">
      <section className="w-full max-w-xl bg-white border border-gray-200 rounded-xl shadow-sm p-6 space-y-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-purple-700">First gym setup</p>
          <h1 className="text-2xl font-bold text-gray-950 mt-1">Create your team workspace</h1>
          <p className="text-sm text-gray-500 mt-1">Start with one owner account and one invite code your teammates can use.</p>
        </div>

        {error && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}

        <form onSubmit={submit} className="space-y-4">
          <label className="block space-y-1 text-sm font-medium text-gray-700">
            Gym name
            <div className="relative">
              <Building2 className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              <input
                value={form.gym_name}
                onChange={(event) => update("gym_name", event.target.value)}
                placeholder="Traktion Jiujitsu Academy"
                className="w-full rounded-lg pl-9 pr-3 py-2 text-sm"
                required
              />
            </div>
          </label>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <label className="block space-y-1 text-sm font-medium text-gray-700">
              Owner email
              <input
                type="email"
                value={form.owner_email}
                onChange={(event) => update("owner_email", event.target.value)}
                placeholder="coach@example.com"
                className="w-full rounded-lg px-3 py-2 text-sm"
                required
              />
            </label>
            <label className="block space-y-1 text-sm font-medium text-gray-700">
              Owner name
              <input
                value={form.owner_name}
                onChange={(event) => update("owner_name", event.target.value)}
                placeholder="Coach name"
                className="w-full rounded-lg px-3 py-2 text-sm"
              />
            </label>
          </div>

          <button disabled={busy} className="w-full bg-purple-700 hover:bg-purple-600 disabled:opacity-60 text-white text-sm font-medium rounded-lg px-4 py-2">
            Create workspace
          </button>
        </form>

        {result && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">Invite code</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm text-gray-900 break-all">{inviteCode}</code>
                <button type="button" onClick={() => navigator.clipboard?.writeText(inviteCode)} className="p-2 rounded-lg border border-gray-200 text-gray-500 hover:text-gray-900" title="Copy invite code">
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <Link to={invitePath} className="inline-flex justify-center items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded-lg px-4 py-2">
                Open invite
              </Link>
              <Link to={`/login?next=${encodeURIComponent("/")}`} className="inline-flex justify-center items-center gap-2 border border-gray-200 text-gray-700 hover:bg-white text-sm font-medium rounded-lg px-4 py-2">
                <KeyRound className="w-4 h-4" /> Sign in as owner
              </Link>
            </div>
          </div>
        )}

        <p className="text-xs text-gray-500">
          Already have an invite? <Link className="text-purple-700 hover:text-purple-600 font-medium" to="/join">Join workspace</Link>
        </p>
      </section>
    </main>
  );
}
