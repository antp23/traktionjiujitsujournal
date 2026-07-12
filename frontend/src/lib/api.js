import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const SESSION_TOKEN_KEY = "bjj_session_token";

export function getSessionToken() {
  return localStorage.getItem(SESSION_TOKEN_KEY);
}

export function setSessionToken(token) {
  localStorage.setItem(SESSION_TOKEN_KEY, token);
}

export function clearSessionToken() {
  localStorage.removeItem(SESSION_TOKEN_KEY);
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: import.meta.env.VITE_API_KEY
    ? { "x-api-key": import.meta.env.VITE_API_KEY }
    : undefined,
});

api.interceptors.request.use((config) => {
  const token = getSessionToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers["x-session-token"] = token;
  }
  return config;
});

// Normalize an axios failure into something safe to render.
export function apiErrorMessage(error, fallback = "Something went wrong. Try again.") {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" && detail ? detail : fallback;
}

// Auth and enrollment
export const requestAuthLink = (email) => api.post("/auth/request-link", { email });
export const consumeAuthLink = (token) => api.post("/auth/consume-link", { token });
export const logout = () => api.post("/auth/logout");
export const getMe = () => api.get("/auth/me");
export const bootstrapWorkspace = (data) => api.post("/workspaces/bootstrap", data);
export const getCurrentWorkspace = () => api.get("/workspaces/current");
export const getInvite = (code) => api.get(`/workspaces/invites/${code}`);
export const joinWorkspace = (inviteCode) => api.post("/workspaces/join", { invite_code: inviteCode });
export const updateProfile = (data) => api.put("/workspaces/profile", data);

// Sessions
export const getSessions = (params) => api.get("/sessions", { params });
export const getSession = (id) => api.get(`/sessions/${id}`);
export const createSession = (data) => api.post("/sessions", data);
export const updateSession = (id, data) => api.put(`/sessions/${id}`, data);
export const deleteSession = (id) => api.delete(`/sessions/${id}`);
export const getSessionStats = () => api.get("/sessions/stats/summary");

// Techniques
export const getTechniques = (params) => api.get("/techniques", { params });
export const getTechnique = (id) => api.get(`/techniques/${id}`);
export const createTechnique = (data) => api.post("/techniques", data);
export const updateTechnique = (id, data) => api.put(`/techniques/${id}`, data);
export const deleteTechnique = (id) => api.delete(`/techniques/${id}`);
export const getSpotlight = () => api.get("/techniques/spotlight");
export const linkTechniques = (id, toId, type) =>
  api.post(`/techniques/${id}/link`, { to_technique_id: toId, relationship_type: type });
export const unlinkTechniques = (id, toId) => api.delete(`/techniques/${id}/link/${toId}`);

// Rolls
export const getRolls = (params) => api.get("/rolls", { params });
export const createRoll = (data) => api.post("/rolls", data);
export const updateRoll = (id, data) => api.put(`/rolls/${id}`, data);
export const deleteRoll = (id) => api.delete(`/rolls/${id}`);
export const getRollStats = () => api.get("/rolls/stats/summary");

// Rank
export const getRankHistory = () => api.get("/rank");
export const getCurrentRank = () => api.get("/rank/current");
export const addRank = (data) => api.post("/rank", data);
export const updateRank = (id, data) => api.put(`/rank/${id}`, data);

// Notes
export const getNotes = (params) => api.get("/notes", { params });
export const getNote = (id) => api.get(`/notes/${id}`);
export const createNote = (data) => api.post("/notes", data);
export const updateNote = (id, data) => api.put(`/notes/${id}`, data);
export const deleteNote = (id) => api.delete(`/notes/${id}`);

// Goals
export const getGoals = () => api.get("/goals");
export const createGoal = (data) => api.post("/goals", data);
export const updateGoal = (id, data) => api.put(`/goals/${id}`, data);

// Sharing
export const createShareThread = (data) => api.post("/sharing/threads", data);
export const getSharedInbox = () => api.get("/sharing/inbox");
export const createThreadMessage = (threadId, data) =>
  api.post(`/sharing/threads/${threadId}/messages`, data);
export const pinThreadMessage = (messageId) => api.post(`/sharing/messages/${messageId}/pin`);

// Dashboard
export const getDashboard = () => api.get("/dashboard");

// Oura
export const getOuraStatus = () => api.get("/oura/status");
export const syncOura = (days = 30) => api.post(`/oura/sync?days=${days}`);
export const getOuraData = (days = 60) => api.get(`/oura/data?days=${days}`);
export const ouraConnectUrl = () => `${API_BASE_URL}/oura/auth`;

// Quick Log
export const parseQuickLog = (text) => api.post("/parse", { text });
