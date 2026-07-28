/* ============================================================
   GITAM CareerHub — Reusable API Service
   src/services/api.js
   ============================================================
   - Axios instance with base URL
   - JWT Bearer token interceptor
   - 401 auto-redirect to login
   - Graceful error handling
   ============================================================ */

const API_BASE_URL = 'http://localhost:8000/api/v1';

/* ── Axios-like fetch wrapper (no build step needed) ───────── */
const CareerHubAPI = {

  _getToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  },

  _getHeaders(extra = {}) {
    const headers = { 'Content-Type': 'application/json', ...extra };
    const token = this._getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
  },

  async _handleResponse(res) {
    if (res.status === 401) {
      localStorage.removeItem('access_token');
      sessionStorage.removeItem('access_token');
      window.location.href = '/landing/login.html';
      throw new Error('Unauthorized — redirecting to login');
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data?.detail || data?.message || `HTTP ${res.status}`);
    }
    return data;
  },

  async get(path, params = {}) {
    const url = new URL(API_BASE_URL + path);
    Object.entries(params).forEach(([k, v]) => v !== undefined && url.searchParams.set(k, v));
    const res = await fetch(url.toString(), { headers: this._getHeaders() });
    return this._handleResponse(res);
  },

  async post(path, body = {}) {
    const res = await fetch(API_BASE_URL + path, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify(body),
    });
    return this._handleResponse(res);
  },

  async put(path, body = {}) {
    const res = await fetch(API_BASE_URL + path, {
      method: 'PUT',
      headers: this._getHeaders(),
      body: JSON.stringify(body),
    });
    return this._handleResponse(res);
  },

  /* ── Auth ──────────────────────────────────────────────── */
  auth: {
    login: (email, password) =>
      CareerHubAPI.post('/auth/login', { email, password }),
    me: () => CareerHubAPI.get('/auth/me'),
  },

  /* ── Dashboard ─────────────────────────────────────────── */
  dashboard: {
    student: () => CareerHubAPI.get('/dashboard/student'),
    recentActivity: () => CareerHubAPI.get('/dashboard/recent-activity'),
  },

  /* ── Students ──────────────────────────────────────────── */
  students: {
    me: () => CareerHubAPI.get('/students/me'),
    update: (data) => CareerHubAPI.put('/students/me', data),
    updateSocialLinks: (data) => CareerHubAPI.put('/students/me/social-links', data),
  },

  /* ── Roadmap ───────────────────────────────────────────── */
  roadmaps: {
    list: (year, semester) => CareerHubAPI.get('/roadmaps', { year, semester }),
    modules: () => CareerHubAPI.get('/roadmaps/modules'),
    progress: () => CareerHubAPI.get('/roadmaps/progress'),
  },

  /* ── Courses ───────────────────────────────────────────── */
  courses: {
    list: () => CareerHubAPI.get('/courses'),
    detail: (id) => CareerHubAPI.get(`/courses/${id}`),
    skills: () => CareerHubAPI.get('/courses/skills'),
  },

  /* ── Projects ──────────────────────────────────────────── */
  projects: {
    list: () => CareerHubAPI.get('/projects'),
    detail: (id) => CareerHubAPI.get(`/projects/${id}`),
  },

  /* ── Certifications ────────────────────────────────────── */
  certifications: {
    list: () => CareerHubAPI.get('/certifications'),
    detail: (id) => CareerHubAPI.get(`/certifications/${id}`),
  },

  /* ── Companies ─────────────────────────────────────────── */
  companies: {
    list: () => CareerHubAPI.get('/companies'),
    detail: (id) => CareerHubAPI.get(`/companies/${id}`),
  },

  /* ── Internships & Placements ──────────────────────────── */
  internships: {
    list: () => CareerHubAPI.get('/internships'),
  },
  placements: {
    list: () => CareerHubAPI.get('/placements'),
    applications: () => CareerHubAPI.get('/applications'),
    offers: () => CareerHubAPI.get('/applications/offers'),
    dashboard: () => CareerHubAPI.get('/applications/dashboard'),
  },

  /* ── AI Mentor ─────────────────────────────────────────── */
  ai: {
    chat: (message, conversationId = null, tool = 'career_advisor') =>
      CareerHubAPI.post('/ai/chat', { message, conversation_id: conversationId, tool, stream: false }),
    conversations: () => CareerHubAPI.get('/ai/conversations'),
    getConversation: (id) => CareerHubAPI.get(`/ai/conversations/${id}`),
    weeklyPlan: () => CareerHubAPI.get('/ai/weekly-plan'),
  },

  /* ── Resume ────────────────────────────────────────────── */
  resume: {
    profile: () => CareerHubAPI.get('/resume'),
    score: () => CareerHubAPI.get('/resume/score'),
    portfolio: () => CareerHubAPI.get('/portfolio'),
  },

  /* ── Gamification / Leaderboard ───────────────────────── */
  gamification: {
    xp: () => CareerHubAPI.get('/gamification/xp'),
    badges: () => CareerHubAPI.get('/gamification/badges'),
    leaderboard: (scope = 'branch') => CareerHubAPI.get('/gamification/leaderboard', { scope }),
    challenges: () => CareerHubAPI.get('/gamification/challenges'),
  },
};

window.CareerHubAPI = CareerHubAPI;
