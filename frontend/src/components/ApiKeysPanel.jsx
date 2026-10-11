import { useCallback, useEffect, useState } from "react";
import { Copy, KeyRound, Trash2 } from "lucide-react";
import { apiErrorMessage, createApiKey, listApiKeys, revokeApiKey } from "../lib/api";

function formatWhen(value) {
  if (!value) return "Never";
  return new Date(`${value}${value.endsWith("Z") ? "" : "Z"}`).toLocaleString();
}

export default function ApiKeysPanel() {
  const [keys, setKeys] = useState([]);
  const [name, setName] = useState("");
  const [newKey, setNewKey] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const response = await listApiKeys();
      setKeys(response.data || []);
    } catch (err) {
      setError(apiErrorMessage(err, "Could not load API keys."));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(event) {
    event.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError("");
    try {
      const response = await createApiKey(name.trim());
      setNewKey(response.data);
      setName("");
      await load();
    } catch (err) {
      setError(apiErrorMessage(err, "Could not create API key."));
    } finally {
      setBusy(false);
    }
  }

  async function handleRevoke(key) {
    if (!window.confirm(`Revoke "${key.name}"? Anything using it will stop working.`)) return;
    setError("");
    try {
      await revokeApiKey(key.key_id);
      if (newKey?.key_id === key.key_id) setNewKey(null);
      await load();
    } catch (err) {
      setError(apiErrorMessage(err, "Could not revoke API key."));
    }
  }

  return (
    <section className="journal-panel invite-panel">
      <div>
        <p className="eyebrow">Integrations</p>
        <h2><KeyRound className="w-4 h-4 inline" /> API access keys</h2>
        <p className="body-copy">
          Personal keys let an assistant or script log sessions for you. Send it as
          <code> Authorization: Bearer &lt;key&gt;</code>. Keys don&apos;t expire; revoke one anytime.
        </p>
      </div>

      {error && <p className="error-strip">{error}</p>}

      <form onSubmit={handleCreate} className="action-row">
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Key name, e.g. Grok Bot"
          maxLength={100}
          aria-label="API key name"
        />
        <button type="submit" className="primary-action" disabled={busy || !name.trim()}>
          Create key
        </button>
      </form>

      {newKey && (
        <div>
          <p className="fine-print">Copy this key now. It won&apos;t be shown again.</p>
          <div className="invite-box">
            <code>{newKey.api_key}</code>
            <button type="button" onClick={() => navigator.clipboard?.writeText(newKey.api_key)} className="icon-action" title="Copy API key">
              <Copy className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {keys.length === 0 ? (
        <p className="fine-print">No active keys.</p>
      ) : (
        <ul>
          {keys.map((key) => (
            <li key={key.key_id} className="invite-box">
              <div>
                <strong>{key.name}</strong> <code>{key.key_prefix}…</code>
                <p className="fine-print">Created {formatWhen(key.created_at)} · Last used {formatWhen(key.last_used_at)}</p>
              </div>
              <button type="button" onClick={() => handleRevoke(key)} className="icon-action" title="Revoke API key">
                <Trash2 className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
