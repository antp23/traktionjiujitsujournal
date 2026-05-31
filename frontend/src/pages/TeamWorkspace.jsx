import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Building2, Copy, Inbox, ShieldCheck, Target, UserRound, UserRoundPlus } from "lucide-react";
import { getCurrentWorkspace } from "../api";
import { useAuth } from "../auth";
import LoadingSpinner from "../components/LoadingSpinner";

export default function TeamWorkspace() {
  const { user, profile, memberships } = useAuth();
  const [workspace, setWorkspace] = useState(null);
  const [membership, setMembership] = useState(null);
  const [invite, setInvite] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await getCurrentWorkspace();
      setWorkspace(response.data.workspace || null);
      setMembership(response.data.membership || null);
      setInvite(response.data.invite || null);
    } catch {
      setError("Could not load team workspace.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner />;

  const role = membership?.role || memberships?.[0]?.role || "athlete";
  const canInvite = ["owner", "coach"].includes(role);
  const inviteUrl = invite?.code ? `${window.location.origin}/join/${invite.code}` : "";

  return (
    <div className="journal-page">
      <section className="journal-header">
        <div>
          <p className="eyebrow">Team workspace</p>
          <h1>{workspace?.gym_name || "Set up the gym"}</h1>
          <p className="lede">This is the team layer for a private mat journal. Coaches only see goals and notes an athlete deliberately sends into shared threads.</p>
        </div>
      </section>

      {error && <p className="error-strip">{error}</p>}

      {!workspace ? (
        <section className="journal-panel workspace-empty">
          <Building2 className="w-5 h-5" />
          <div>
            <h2>No workspace yet</h2>
            <p>Create the team workspace, or join with an invite code from your coach.</p>
          </div>
          <div className="action-row">
            <Link to="/setup" className="primary-action">
              <UserRoundPlus className="w-4 h-4" /> Create workspace
            </Link>
            <Link to="/join" className="quiet-action">Join with invite</Link>
          </div>
        </section>
      ) : (
        <>
          <section className="workspace-card">
            <div>
              <p className="eyebrow">Current account</p>
              <h2>{workspace.gym_name}</h2>
              <p>{user?.email} · {role}</p>
            </div>
            <Link to="/onboarding" className="quiet-action">
              <UserRound className="w-4 h-4" /> Edit profile
            </Link>
          </section>

          <section className="journal-panel privacy-panel">
            <ShieldCheck className="w-5 h-5" />
            <div>
              <h2>Sharing rules are deliberate</h2>
              <p className="body-copy">
                Session history, techniques, recovery notes, and private notes stay in the athlete account unless a goal or note is sent to Coach Inbox.
              </p>
            </div>
          </section>

          {canInvite && invite?.code && (
            <section className="journal-panel invite-panel">
              <div>
                <p className="eyebrow">Team invite</p>
                <h2>Self-enrollment link</h2>
                <p className="body-copy">Share this with teammates when you are ready to enroll them. New members create their own account, fill out a profile, and choose what to share.</p>
              </div>
              <div className="invite-box">
                <code>{inviteUrl}</code>
                <button type="button" onClick={() => navigator.clipboard?.writeText(inviteUrl)} className="icon-action" title="Copy invite link">
                  <Copy className="w-4 h-4" />
                </button>
              </div>
              <p className="fine-print">Invite code: {invite.code}</p>
            </section>
          )}

          <section className="workspace-grid">
            <Link to="/goals" className="workspace-tile">
              <Target className="w-5 h-5" />
              <h3>Goals</h3>
              <p>Track private work first. Use Ask coach to create a shared thread for selected goals.</p>
            </Link>
            <Link to="/inbox" className="workspace-tile">
              <Inbox className="w-5 h-5" />
              <h3>Coach inbox</h3>
              <p>Only athlete-sent goal and note threads appear here. Pinned replies become durable coach notes.</p>
            </Link>
            <div className="workspace-tile">
              <UserRound className="w-5 h-5" />
              <h3>WhatsApp contact</h3>
              <p>{profile?.whatsapp_phone || "No phone added yet."}</p>
              <p className="fine-print">Optional contact detail only. WhatsApp message capture is not enabled for this launch.</p>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
