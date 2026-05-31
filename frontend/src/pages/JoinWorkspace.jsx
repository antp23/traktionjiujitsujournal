import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowRight, Building2 } from "lucide-react";
import { getInvite, joinWorkspace } from "../api";
import { useAuth } from "../auth";

export default function JoinWorkspace() {
  const { code: pathCode } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { isAuthenticated, memberships, profile, refreshMe } = useAuth();
  const initialCode = pathCode || searchParams.get("invite") || searchParams.get("code") || "";
  const [inviteCode, setInviteCode] = useState(initialCode);
  const [invite, setInvite] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const trimmedCode = useMemo(() => inviteCode.trim(), [inviteCode]);

  const loadInvite = useCallback(async (code) => {
    if (!code) {
      setInvite(null);
      return;
    }

    try {
      const response = await getInvite(code);
      setInvite(response.data);
      setError("");
    } catch {
      setInvite(null);
      setError("Invite code was not found or is no longer usable.");
    }
  }, []);

  useEffect(() => {
    if (initialCode) {
      loadInvite(initialCode);
    }
  }, [initialCode, loadInvite]);

  useEffect(() => {
    if (memberships.length && profile) {
      navigate("/", { replace: true });
    }
  }, [memberships.length, navigate, profile]);

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    if (!isAuthenticated) {
      navigate(`/login?next=${encodeURIComponent(`/join/${trimmedCode}`)}`);
      return;
    }

    setBusy(true);
    try {
      await joinWorkspace(trimmedCode);
      await refreshMe();
      navigate("/onboarding", { replace: true });
    } catch {
      setError("Could not join this workspace. Check the invite and try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-purple-700">Team enrollment</p>
        <h1 className="text-2xl font-bold text-gray-950 mt-1">Join workspace</h1>
        <p className="text-sm text-gray-500 mt-1">Enter your gym invite code to connect your private journal to a team workspace.</p>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}

      <form onSubmit={submit} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
        <label className="block text-sm font-medium text-gray-700" htmlFor="invite">Invite code</label>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            id="invite"
            value={inviteCode}
            onChange={(event) => setInviteCode(event.target.value)}
            onBlur={() => loadInvite(trimmedCode)}
            placeholder="abc123"
            className="flex-1 rounded-lg px-3 py-2 text-sm"
            required
          />
          <button type="button" onClick={() => loadInvite(trimmedCode)} className="px-4 py-2 rounded-lg border border-gray-200 text-sm text-gray-700 hover:bg-gray-50">
            Check
          </button>
        </div>

        {invite && (
          <div className="flex items-start gap-3 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <Building2 className="w-4 h-4 text-purple-700 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-gray-900">{invite.gym_name || invite.workspace?.gym_name || "Gym workspace"}</p>
              <p className="text-xs text-gray-500">{invite.usable === false ? "This invite is not usable." : "Invite is available."}</p>
            </div>
          </div>
        )}

        {!isAuthenticated && (
          <p className="text-sm text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
            Sign in first, then this invite code will be used automatically.
          </p>
        )}

        <button disabled={busy || !trimmedCode} className="inline-flex items-center gap-2 bg-purple-700 hover:bg-purple-600 disabled:opacity-60 text-white text-sm font-medium rounded-lg px-4 py-2">
          Join workspace <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {!isAuthenticated && (
        <Link to={`/login?next=${encodeURIComponent(`/join/${trimmedCode}`)}`} className="text-sm text-purple-700 hover:text-purple-600 font-medium">
          Sign in to continue
        </Link>
      )}
    </div>
  );
}
