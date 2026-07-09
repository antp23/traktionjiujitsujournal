import { useCallback, useEffect, useMemo, useState } from "react";
import { AuthContext } from "./authContext";
import {
  clearSessionToken,
  consumeAuthLink,
  getMe,
  getSessionToken,
  logout,
  setSessionToken,
} from "./api";

export function AuthProvider({ children }) {
  const [sessionToken, setSessionTokenState] = useState(() => getSessionToken());
  const [user, setUser] = useState(null);
  const [memberships, setMemberships] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(Boolean(sessionToken));

  const resetState = useCallback(() => {
    setUser(null);
    setMemberships([]);
    setProfile(null);
  }, []);

  const refreshMe = useCallback(async () => {
    if (!getSessionToken()) {
      resetState();
      setLoading(false);
      return null;
    }

    setLoading(true);
    try {
      const response = await getMe();
      setUser(response.data.user);
      setMemberships(response.data.memberships || []);
      setProfile(response.data.profile || null);
      return response.data;
    } catch (error) {
      clearSessionToken();
      setSessionTokenState(null);
      resetState();
      throw error;
    } finally {
      setLoading(false);
    }
  }, [resetState]);

  useEffect(() => {
    if (sessionToken) {
      refreshMe().catch(() => {});
    }
  }, [refreshMe, sessionToken]);

  const consumeToken = useCallback(async (token) => {
    const response = await consumeAuthLink(token);
    setSessionToken(response.data.session_token);
    setSessionTokenState(response.data.session_token);
    setUser(response.data.user);
    await refreshMe().catch(() => null);
    return response.data;
  }, [refreshMe]);

  const signOut = useCallback(() => {
    // Revoke the server-side session too; local cleanup happens regardless.
    logout().catch(() => {});
    clearSessionToken();
    setSessionTokenState(null);
    resetState();
  }, [resetState]);

  const value = useMemo(() => ({
    sessionToken,
    user,
    memberships,
    profile,
    loading,
    isAuthenticated: Boolean(sessionToken),
    consumeToken,
    refreshMe,
    signOut,
  }), [consumeToken, loading, memberships, profile, refreshMe, sessionToken, signOut, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
