import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { KeyRound, Mail } from "lucide-react";
import { requestAuthLink } from "../api";
import { useAuth } from "../auth";

function nextPath(searchParams, fallback = "/") {
  const next = searchParams.get("next");
  return next && next.startsWith("/") ? next : fallback;
}

export default function Login() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { consumeToken, isAuthenticated } = useAuth();
  const [email, setEmail] = useState("");
  const [token, setToken] = useState(searchParams.get("token") || "");
  const [devToken, setDevToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const consumedQueryToken = useRef(false);

  useEffect(() => {
    if (isAuthenticated && !searchParams.get("token")) {
      navigate(nextPath(searchParams), { replace: true });
    }
  }, [isAuthenticated, navigate, searchParams]);

  useEffect(() => {
    const queryToken = searchParams.get("token");
    if (!queryToken || consumedQueryToken.current) return;
    consumedQueryToken.current = true;

    setBusy(true);
    consumeToken(queryToken)
      .then(() => navigate(nextPath(searchParams), { replace: true }))
      .catch(() => setError("That login token did not work. Request a new one and try again."))
      .finally(() => setBusy(false));
  }, [consumeToken, navigate, searchParams]);

  const requestLink = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);

    try {
      const response = await requestAuthLink(email.trim());
      setDevToken(response.data.dev_token || "");
      setToken(response.data.dev_token || "");
      setMessage(response.data.dev_token
        ? "Dev login token created."
        : response.data.message || "If this email is allowed, a sign-in link will be sent.");
    } catch {
      setError("Could not create a login link. Check the backend and try again.");
    } finally {
      setBusy(false);
    }
  };

  const consume = async (event) => {
    event.preventDefault();
    setError("");
    setBusy(true);

    try {
      await consumeToken(token.trim());
      navigate(nextPath(searchParams), { replace: true });
    } catch {
      setError("That login token did not work. Request a new one and try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 flex items-center justify-center">
      <section className="w-full max-w-md bg-white border border-gray-200 rounded-xl shadow-sm p-6 space-y-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-purple-700">BJJ Tracker</p>
          <h1 className="text-2xl font-bold text-gray-950 mt-1">Sign in</h1>
          <p className="text-sm text-gray-500 mt-1">Request a sign-in link for your private training journal. Local pilots may show a dev token below.</p>
        </div>

        {error && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}
        {message && <p className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">{message}</p>}

        <form onSubmit={requestLink} className="space-y-3">
          <label className="block text-sm font-medium text-gray-700" htmlFor="email">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="athlete@example.com"
              className="w-full rounded-lg pl-9 pr-3 py-2 text-sm"
              required
            />
          </div>
          <button disabled={busy} className="w-full bg-purple-700 hover:bg-purple-600 disabled:opacity-60 text-white text-sm font-medium rounded-lg px-4 py-2">
            Request sign-in link
          </button>
        </form>

        {devToken && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-xs font-medium text-gray-500 mb-1">Dev token</p>
            <code className="block text-xs text-gray-900 break-all">{devToken}</code>
          </div>
        )}

        <form onSubmit={consume} className="space-y-3">
          <label className="block text-sm font-medium text-gray-700" htmlFor="token">Token</label>
          <div className="relative">
            <KeyRound className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
            <input
              id="token"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              placeholder="Paste token from sign-in link"
              className="w-full rounded-lg pl-9 pr-3 py-2 text-sm"
              required
            />
          </div>
          <button disabled={busy} className="w-full bg-slate-900 hover:bg-slate-800 disabled:opacity-60 text-white text-sm font-medium rounded-lg px-4 py-2">
            Continue
          </button>
        </form>

        <p className="text-xs text-gray-500">
          Joining from an invite? <Link className="text-purple-700 hover:text-purple-600 font-medium" to="/join">Enter invite code</Link>
        </p>
        <p className="text-xs text-gray-500">
          Starting a gym workspace? <Link className="text-purple-700 hover:text-purple-600 font-medium" to="/setup">Create setup invite</Link>
        </p>
      </section>
    </main>
  );
}
