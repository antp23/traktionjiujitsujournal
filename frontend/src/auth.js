import { createContext, createElement, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { consumeAuthLink, getMe } from "./api";

const SESSION_TOKEN_KEY = "bjj_session_token";

const AuthContext = createContext(null);

export function getSessionToken() {
  return localStorage.getItem(SESSION_TOKEN_KEY);
}

export function setSessionToken(token) {
  localStorage.setItem(SESSION_TOKEN_KEY, token);
}

export function clearSessionToken() {
  localStorage.removeItem(SESSION_TOKEN_KEY);
}

export function AuthProvider({ children }) {
  const [sessionToken, setSessionTokenState] = useState(() => getSessionToken());
  const [user, setUser] = useState(null);
  const [memberships, setMemberships] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(Boolean(sessionToken));

  const refreshMe = useCallback(async () => {
    if (!getSessionToken()) {
      setUser(null);
      setMemberships([]);
      setProfile(null);
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
      setUser(null);
      setMemberships([]);
      setProfile(null);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

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
    clearSessionToken();
    setSessionTokenState(null);
    setUser(null);
    setMemberships([]);
    setProfile(null);
  }, []);

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

  return createElement(AuthContext.Provider, { value }, children);
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
