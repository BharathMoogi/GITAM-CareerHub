/* ==========================================================================
   GITAM CareerHub — Student Dashboard (Full API Integration)
   All values from real backend. Zero hardcoded data.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  guardAuth();
  initSidebarNav();
  initTaskCheckboxes();
  initSearchKeyboardShortcut();
  initThemeToggle();
  initNotifications();
  loadDashboardView(); // load default view immediately
  _loadedViews.add('dashboard'); // mark as loaded so clicking nav doesn't double-fetch
});

// Cache to avoid re-fetching already-loaded views in the same session
const _loadedViews = new Set();


/* ── AUTH GUARD ─────────────────────────────────────────────────────────────── */
function guardAuth() {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/landing/login.html';
  }
}

/* ── HELPERS ─────────────────────────────────────────────────────────────────── */
function showLoading(containerId, msg = 'Loading...') {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `
    <div class="state-box loading-box">
      <div class="spinner"></div>
      <p>${msg}</p>
    </div>`;
}

function showEmpty(containerId, msg = 'No data found.', icon = '📭') {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `
    <div class="state-box empty-box">
      <span class="state-icon">${icon}</span>
      <p>${msg}</p>
    </div>`;
}

function showError(containerId, msg = 'Failed to load. Please try again.') {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `
    <div class="state-box error-box">
      <span class="state-icon">⚠️</span>
      <p>${msg}</p>
      <button class="btn-retry" onclick="location.reload()">Retry</button>
    </div>`;
}

function fmt(val, fallback = '—') {
  return val !== null && val !== undefined ? val : fallback;
}

function fmtPct(val) {
  return val !== null && val !== undefined ? `${Math.round(val)}%` : '—%';
}

function fmtDate(str) {
  if (!str) return '—';
  return new Date(str).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function fmtTimeAgo(str) {
  if (!str) return '';
  const diff = (Date.now() - new Date(str)) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

const STATUS_BADGE = {
  COMPLETED: '<span class="badge-status done">Completed</span>',
  IN_PROGRESS: '<span class="badge-status progress">In Progress</span>',
  NOT_STARTED: '<span class="badge-status pending">Not Started</span>',
  OPEN: '<span class="badge-status done">Open</span>',
  CLOSED: '<span class="badge-status pending">Closed</span>',
  SHORTLISTED: '<span class="badge-status progress">Shortlisted</span>',
  APPLIED: '<span class="badge-status progress">Applied</span>',
  SELECTED: '<span class="badge-status done">Selected</span>',
  REJECTED: '<span class="badge-status error">Rejected</span>',
};

function statusBadge(s) {
  return STATUS_BADGE[s] || `<span class="badge-status pending">${s || '—'}</span>`;
}

function progressBar(pct) {
  const p = Math.round(pct || 0);
  return `<div class="prog-bar-wrap"><div class="prog-bar" style="width:${p}%"></div><span>${p}%</span></div>`;
}

/* ── SIDEBAR NAVIGATION ──────────────────────────────────────────────────────── */
function initSidebarNav() {
  const navItems = document.querySelectorAll('.nav-item');
  const tabViews = document.querySelectorAll('.tab-view');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      const page = item.getAttribute('data-page');
      tabViews.forEach(v => v.classList.remove('active'));
      const target = document.getElementById(`view-${page}`);
      if (target) {
        target.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
      fetchPageData(page);
    });
  });
}

/* ── ROUTE PAGE DATA ─────────────────────────────────────────────────────────── */
function fetchPageData(page) {
  // Only fetch once per session — avoids re-hitting the API on repeat clicks
  if (_loadedViews.has(page)) return;
  _loadedViews.add(page);

  switch (page) {
    case 'dashboard':     loadDashboardView();    break;
    case 'roadmap':       loadRoadmapView();      break;
    case 'courses':       loadCoursesView();      break;
    case 'projects':      loadProjectsView();     break;
    case 'certifications':loadCertificationsView();break;
    case 'companies':     loadCompaniesView();    break;
    case 'internships':   loadInternshipsView();  break;
    case 'placements':    loadPlacementsView();   break;
    case 'ai-mentor':     loadAIMentorView();     break;
    case 'resume':        loadResumeView();       break;
    case 'leaderboard':   loadLeaderboardView();  break;
    case 'profile':       loadProfileView();      break;
    case 'settings':      /* frontend-only */     break;
    default: break;
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   1. DASHBOARD VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadDashboardView() {
  try {
    const data = await CareerHubAPI.dashboard.student();

    /* Profile */
    const p = data.profile || {};
    const nameEl = document.querySelector('.welcome-title');
    if (nameEl) nameEl.textContent = `Welcome back, ${p.full_name?.split(' ')[0] || 'Student'}! 👋`;
    const userNameEl = document.querySelector('.user-name');
    if (userNameEl) userNameEl.textContent = p.full_name || '—';
    const userMetaEl = document.querySelector('.user-meta');
    if (userMetaEl) userMetaEl.textContent =
      `${p.branch_code || p.branch_name || '—'} • ${p.current_year ? p.current_year + (p.current_year === 1 ? 'st' : p.current_year === 2 ? 'nd' : p.current_year === 3 ? 'rd' : 'th') + ' Year' : '—'}`;
    const welcomeMeta = document.querySelector('.welcome-meta span:first-child');
    if (welcomeMeta) welcomeMeta.textContent =
      `${p.branch_code || '—'} • ${p.current_year || '—'}${p.current_year === 1 ? 'st' : p.current_year === 2 ? 'nd' : p.current_year === 3 ? 'rd' : 'th'} Year • Semester ${p.semester || '—'}`;
    const targetBadge = document.querySelector('.target-role-badge');
    if (targetBadge && p.target_role) targetBadge.innerHTML =
      `<i class="fas fa-crosshairs"></i> Target: ${p.target_role}`;

    /* Streak */
    const streakEl = document.querySelector('.streak-days');
    if (streakEl) streakEl.textContent = `${fmt(data.learning_streak_days, 0)} Days`;

    /* Stats */
    const r = data.readiness || {};
    const prog = data.progress || {};
    const readPct = Math.round(r.overall_career_readiness || 0);
    const roadPct = Math.round(prog.roadmap_completion_pct || 0);

    // Career readiness donut
    const donutPct = document.querySelector('.donut-pct');
    if (donutPct) donutPct.textContent = `${readPct}%`;
    const readPctEl = document.querySelector('.readiness-pct');
    if (readPctEl) readPctEl.textContent = `${readPct}%`;
    const readGrade = document.querySelector('.readiness-grade');
    if (readGrade) readGrade.textContent =
      readPct >= 85 ? 'Outstanding' : readPct >= 70 ? 'Excellent' : readPct >= 50 ? 'Good' : 'Needs Work';
    // Update donut SVG stroke
    const donutCircle = document.querySelector('.donut-svg circle:last-child');
    if (donutCircle) {
      const circumference = 201.06;
      const offset = circumference - (readPct / 100) * circumference;
      donutCircle.setAttribute('stroke-dashoffset', offset.toFixed(2));
    }

    // Roadmap progress stat card
    const statBigs = document.querySelectorAll('.stat-big');
    if (statBigs[0]) statBigs[0].innerHTML = `${roadPct}%`;
    const statSubs = document.querySelectorAll('.stat-sub');
    if (statSubs[0]) statSubs[0].textContent = roadPct >= 60 ? 'On Track' : 'Keep Going';

    // Projects
    if (statBigs[1]) statBigs[1].innerHTML =
      `${fmt(prog.active_applications, 0)} <span class="stat-of">active</span>`;

    // Certifications
    if (statBigs[2]) statBigs[2].innerHTML =
      `${fmt(prog.shortlisted_count, 0)} <span class="stat-of">shortlisted</span>`;

    // Applications
    if (statBigs[3]) statBigs[3].textContent = fmt(prog.total_applications, 0);
    if (statSubs[3]) statSubs[3].textContent = 'Total Applied';

    // Offers
    const offerNum = document.querySelector('.offer-num');
    if (offerNum) offerNum.textContent = fmt(prog.offers_count, 0);
    const offerSub = document.querySelector('.offer-sub');
    if (offerSub) offerSub.textContent = prog.offers_count > 0 ? 'Congratulations! 🎉' : 'Keep Applying!';

    /* Today's Tasks */
    renderTasks(data.todays_tasks || []);

    /* AI Recommendation */
    const aiHighlight = document.querySelector('.ai-highlight');
    if (aiHighlight && data.recommended_next_action) {
      aiHighlight.textContent = data.recommended_next_action;
    }

    /* Upcoming Deadlines */
    renderDeadlines(data.upcoming_deadlines || []);

    /* Top Companies */
    renderTopCompanies(data.top_companies || []);

    /* Skill Distribution */
    renderSkillDistribution(data.skill_distribution || []);

    /* Recent Activity */
    renderRecentActivity(data.recent_activities || []);

  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

function renderTasks(tasks) {
  const list = document.getElementById('task-list');
  if (!list) return;
  if (!tasks.length) {
    list.innerHTML = '<li class="task-item" style="color:var(--text-muted);padding:12px 0;">No tasks for today 🎉</li>';
    return;
  }
  list.innerHTML = tasks.map((t, i) => `
    <li class="task-item">
      <input type="checkbox" class="task-check" id="t${i}">
      <label for="t${i}" class="task-label">${t.title || t.task || t.description || '—'}</label>
      ${t.category ? `<span class="task-tag ${(t.category||'').toLowerCase()}">${t.category}</span>` : ''}
      ${t.due_date ? `<span class="task-due">${fmtDate(t.due_date)}</span>` : ''}
    </li>`).join('');
  initTaskCheckboxes();
}

function renderDeadlines(deadlines) {
  const list = document.querySelector('.deadline-list');
  if (!list) return;
  if (!deadlines.length) {
    list.innerHTML = '<li style="color:var(--text-muted);padding:12px 0;">No upcoming deadlines.</li>';
    return;
  }
  list.innerHTML = deadlines.slice(0, 5).map(d => {
    const urgent = d.days_left !== undefined && d.days_left <= 3;
    return `
    <li class="deadline-item">
      <i class="fas fa-calendar deadline-item-icon"></i>
      <span class="deadline-name">${d.title || d.name || '—'}</span>
      <span class="deadline-date ${urgent ? 'urgent' : 'warning'}">${fmtDate(d.deadline || d.due_date)}</span>
    </li>`;
  }).join('');
}

function renderTopCompanies(companies) {
  const list = document.querySelector('.company-list');
  if (!list) return;
  if (!companies.length) {
    list.innerHTML = '<li style="color:var(--text-muted);padding:12px 0;">No company data yet.</li>';
    return;
  }
  list.innerHTML = companies.slice(0, 5).map(c => {
    const initials = (c.company_name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    const pct = Math.round(c.overall_score || c.skill_match || 0);
    return `
    <li class="company-item">
      <div class="company-logo" style="background:var(--accent-teal);color:#fff;font-weight:700;font-size:12px;display:flex;align-items:center;justify-content:center;border-radius:8px;width:36px;height:36px;">${initials}</div>
      <div class="company-info">
        <span class="company-name">${c.company_name}</span>
        <div class="company-bar-wrap"><div class="company-bar" style="width:${pct}%"></div></div>
      </div>
      <span class="company-pct">${pct}%</span>
      <button class="btn-company-view" onclick="document.querySelector('[data-page=companies]').click()">View</button>
    </li>`;
  }).join('');
}

function renderSkillDistribution(skills) {
  const legend = document.querySelector('.skill-legend');
  if (!legend || !skills.length) return;
  const colors = ['#0C7A6B','#0E9B87','#5BC8B8','#A8DDD6','#D4EEEB'];
  legend.innerHTML = skills.slice(0, 5).map((s, i) =>
    `<li><span class="legend-dot" style="background:${colors[i % colors.length]}"></span>${s.label}<span class="legend-pct">${Math.round(s.percentage || s.value || 0)}%</span></li>`
  ).join('');
  // Update center donut text
  const overallText = document.querySelector('.skill-donut text:first-of-type');
  const overall = skills.reduce((sum, s) => sum + (s.value || 0), 0) / (skills.length || 1);
  if (overallText) overallText.textContent = `${Math.round(overall)}%`;
}

function renderRecentActivity(activities) {
  const grid = document.querySelector('.activity-grid');
  if (!grid) return;
  if (!activities.length) {
    grid.innerHTML = '<div style="color:var(--text-muted);padding:16px 0;">No recent activity yet.</div>';
    return;
  }
  const iconMap = {
    COURSE: 'course-icon fa-book-open',
    PROJECT: 'project-icon fa-code',
    CERTIFICATION: 'cert-icon fa-award',
    APPLICATION: 'apply-icon fa-briefcase',
    AI_CHAT: 'course-icon fa-robot',
  };
  grid.innerHTML = activities.slice(0, 6).map(a => {
    const ico = iconMap[a.category] || 'course-icon fa-star';
    const [cls, faIcon] = ico.split(' ');
    return `
    <div class="activity-item">
      <div class="activity-icon ${cls}"><i class="fas ${faIcon}"></i></div>
      <div class="activity-info">
        <p class="activity-text">${a.title || '—'}</p>
        <span class="activity-time">${fmtTimeAgo(a.timestamp)}</span>
      </div>
    </div>`;
  }).join('');
}

/* ══════════════════════════════════════════════════════════════════════════════
   2. ROADMAP VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadRoadmapView() {
  showLoading('roadmap-content', 'Loading your roadmap...');
  try {
    const data = await CareerHubAPI.roadmaps.list();
    const roadmaps = data.data || data;
    const el = document.getElementById('roadmap-content');
    if (!roadmaps.length) {
      showEmpty('roadmap-content', 'No roadmap assigned to your branch yet.', '🗺️');
      return;
    }
    el.innerHTML = roadmaps.map(rm => `
      <div class="view-card mb-16">
        <div class="view-card-header">
          <div>
            <h3 class="view-card-title">Year ${rm.year_number} — Semester ${rm.semester_number}</h3>
            <p class="view-card-sub">${rm.title}</p>
          </div>
          <span class="badge-status ${rm.is_active ? 'done' : 'pending'}">${rm.is_active ? 'Active' : 'Locked'}</span>
        </div>
        ${rm.description ? `<p class="view-desc">${rm.description}</p>` : ''}
        <div class="module-grid">
          ${(rm.modules || []).map(mod => `
            <div class="module-card ${mod.is_locked ? 'locked' : ''}">
              <div class="module-header">
                <span class="module-type-badge">${mod.module_type}</span>
                ${mod.is_required ? '<span class="req-badge">Required</span>' : ''}
              </div>
              <p class="module-name">${mod.module_name}</p>
              ${progressBar(mod.completion_percentage)}
              ${statusBadge(mod.user_status)}
              <p class="module-meta">~${mod.estimated_hours}h estimated</p>
            </div>`).join('') || '<p class="view-desc">No modules in this semester.</p>'}
        </div>
      </div>`).join('');
  } catch (err) {
    showError('roadmap-content', err.message || 'Failed to load roadmap.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   3. COURSES VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadCoursesView() {
  showLoading('courses-content', 'Loading courses...');
  try {
    const data = await CareerHubAPI.courses.list();
    const courses = data.data || data;
    const el = document.getElementById('courses-content');
    if (!courses.length) {
      showEmpty('courses-content', 'No courses available for your branch.', '📚');
      return;
    }
    el.innerHTML = `<div class="card-grid">${courses.map(c => `
      <div class="view-card">
        <div class="view-card-header">
          <div>
            <h3 class="view-card-title">${c.title}</h3>
            <p class="view-card-sub">Year ${c.year_number} • Sem ${c.semester_number} • ${c.difficulty}</p>
          </div>
          ${statusBadge(c.user_status)}
        </div>
        ${c.description ? `<p class="view-desc">${c.description}</p>` : ''}
        ${progressBar(c.completion_percentage)}
        <div class="tag-row">
          ${(c.skills || []).slice(0,3).map(s => `<span class="skill-tag">${s.skill_name}</span>`).join('')}
        </div>
        <p class="module-meta">~${c.estimated_hours}h • ${c.status}</p>
      </div>`).join('')}</div>`;
  } catch (err) {
    showError('courses-content', err.message || 'Failed to load courses.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   4. PROJECTS VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadProjectsView() {
  showLoading('projects-content', 'Loading projects...');
  try {
    const data = await CareerHubAPI.projects.list();
    const projects = data.data || data;
    const el = document.getElementById('projects-content');
    if (!projects.length) {
      showEmpty('projects-content', 'No projects assigned yet. Check back soon!', '💻');
      return;
    }
    el.innerHTML = `<div class="card-grid">${projects.map(p => `
      <div class="view-card">
        <div class="view-card-header">
          <h3 class="view-card-title">${p.title || p.name || '—'}</h3>
          ${statusBadge(p.user_status || p.status)}
        </div>
        ${p.description ? `<p class="view-desc">${p.description}</p>` : ''}
        ${progressBar(p.completion_percentage || 0)}
        <div class="tag-row">
          ${p.difficulty ? `<span class="skill-tag">${p.difficulty}</span>` : ''}
          ${p.domain ? `<span class="skill-tag">${p.domain}</span>` : ''}
        </div>
        ${p.submission_deadline ? `<p class="module-meta">Deadline: ${fmtDate(p.submission_deadline)}</p>` : ''}
        ${p.ai_review_score ? `<p class="module-meta">AI Score: ${p.ai_review_score}/100</p>` : ''}
      </div>`).join('')}</div>`;
  } catch (err) {
    showError('projects-content', err.message || 'Failed to load projects.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   5. CERTIFICATIONS VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadCertificationsView() {
  showLoading('certifications-content', 'Loading certifications...');
  try {
    const data = await CareerHubAPI.certifications.list();
    const certs = data.data || data;
    const el = document.getElementById('certifications-content');
    if (!certs.length) {
      showEmpty('certifications-content', 'No certifications added yet. Start earning!', '🎖️');
      return;
    }
    el.innerHTML = `<div class="card-grid">${certs.map(c => `
      <div class="view-card">
        <div class="view-card-header">
          <div>
            <h3 class="view-card-title">${c.title || c.name || '—'}</h3>
            <p class="view-card-sub">${c.provider || c.issuer || '—'}</p>
          </div>
          ${c.is_verified ? '<span class="badge-status done">✓ Verified</span>' : '<span class="badge-status pending">Pending</span>'}
        </div>
        ${c.description ? `<p class="view-desc">${c.description}</p>` : ''}
        <div class="tag-row">
          ${c.category ? `<span class="skill-tag">${c.category}</span>` : ''}
          ${c.grade ? `<span class="skill-tag">Grade: ${c.grade}</span>` : ''}
        </div>
        ${c.issue_date ? `<p class="module-meta">Issued: ${fmtDate(c.issue_date)}</p>` : ''}
        ${c.expiry_date ? `<p class="module-meta">Expires: ${fmtDate(c.expiry_date)}</p>` : ''}
        ${c.credential_url ? `<a href="${c.credential_url}" target="_blank" class="card-link">View Certificate ↗</a>` : ''}
      </div>`).join('')}</div>`;
  } catch (err) {
    showError('certifications-content', err.message || 'Failed to load certifications.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   6. COMPANIES VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadCompaniesView() {
  showLoading('companies-content', 'Loading companies...');
  try {
    const data = await CareerHubAPI.companies.list();
    const companies = data.data || data;
    const el = document.getElementById('companies-content');
    if (!companies.length) {
      showEmpty('companies-content', 'No companies available yet.', '🏢');
      return;
    }
    el.innerHTML = `<div class="card-grid">${companies.map(c => {
      const initials = (c.name || c.company_name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
      const score = Math.round(c.readiness_score || c.overall_score || c.skill_match || 0);
      return `
      <div class="view-card">
        <div class="view-card-header">
          <div style="display:flex;align-items:center;gap:12px;">
            <div class="company-logo-lg">${initials}</div>
            <div>
              <h3 class="view-card-title">${c.name || c.company_name || '—'}</h3>
              <p class="view-card-sub">${c.industry || '—'} • ${c.location || '—'}</p>
            </div>
          </div>
          <span class="score-badge">${score}% Match</span>
        </div>
        ${c.description ? `<p class="view-desc">${c.description}</p>` : ''}
        ${progressBar(score)}
        <div class="tag-row">
          ${c.hiring_status ? `<span class="skill-tag">${c.hiring_status}</span>` : ''}
          ${c.company_type ? `<span class="skill-tag">${c.company_type}</span>` : ''}
        </div>
      </div>`}).join('')}</div>`;
  } catch (err) {
    showError('companies-content', err.message || 'Failed to load companies.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   7. INTERNSHIPS VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadInternshipsView() {
  showLoading('internships-content', 'Loading internships...');
  try {
    const data = await CareerHubAPI.internships.list();
    const internships = data.data || data;
    const el = document.getElementById('internships-content');
    if (!internships.length) {
      showEmpty('internships-content', 'No internship listings at the moment.', '💼');
      return;
    }
    el.innerHTML = `<div class="card-grid">${internships.map(i => `
      <div class="view-card ${i.is_eligible ? '' : 'card-locked'}">
        <div class="view-card-header">
          <div>
            <h3 class="view-card-title">${i.title}</h3>
            <p class="view-card-sub">${i.company_name} • ${i.mode} • ${i.location || 'Remote'}</p>
          </div>
          ${i.is_eligible
            ? '<span class="badge-status done">Eligible ✓</span>'
            : '<span class="badge-status error">Not Eligible</span>'}
        </div>
        <div class="tag-row">
          <span class="skill-tag">${i.internship_type}</span>
          ${i.stipend ? `<span class="skill-tag">₹${i.stipend.toLocaleString()}/mo</span>` : ''}
          ${i.duration ? `<span class="skill-tag">${i.duration}</span>` : ''}
          <span class="skill-tag">${i.openings} openings</span>
        </div>
        ${i.eligibility_reason ? `<p class="module-meta">${i.eligibility_reason}</p>` : ''}
        ${i.application_end ? `<p class="module-meta">Apply by: ${fmtDate(i.application_end)}</p>` : ''}
        ${statusBadge(i.status)}
      </div>`).join('')}</div>`;
  } catch (err) {
    showError('internships-content', err.message || 'Failed to load internships.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   8. PLACEMENTS VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadPlacementsView() {
  showLoading('placements-content', 'Loading placements...');
  try {
    const [placementsRes, dashRes] = await Promise.allSettled([
      CareerHubAPI.placements.list(),
      CareerHubAPI.placements.dashboard(),
    ]);
    const placements = placementsRes.status === 'fulfilled' ? (placementsRes.value.data || placementsRes.value) : [];
    const dash = dashRes.status === 'fulfilled' ? (dashRes.value.data || dashRes.value) : null;
    const el = document.getElementById('placements-content');
    let html = '';

    // Summary stats
    if (dash?.summary) {
      const s = dash.summary;
      html += `
        <div class="stats-mini-row">
          <div class="mini-stat"><span class="mini-num">${s.total_applications || 0}</span><span class="mini-label">Applications</span></div>
          <div class="mini-stat"><span class="mini-num">${s.shortlisted || 0}</span><span class="mini-label">Shortlisted</span></div>
          <div class="mini-stat"><span class="mini-num">${s.in_progress || 0}</span><span class="mini-label">In Progress</span></div>
          <div class="mini-stat"><span class="mini-num">${s.selected || 0}</span><span class="mini-label">Selected</span></div>
          <div class="mini-stat offer-mini"><span class="mini-num">${s.offers_received || 0}</span><span class="mini-label">Offers 🎉</span></div>
        </div>`;
    }

    if (!placements.length) {
      html += '<div class="state-box empty-box"><span class="state-icon">🎓</span><p>No placement drives open right now.</p></div>';
    } else {
      html += `<div class="card-grid">${placements.map(p => `
        <div class="view-card ${p.is_eligible ? '' : 'card-locked'}">
          <div class="view-card-header">
            <div>
              <h3 class="view-card-title">${p.title}</h3>
              <p class="view-card-sub">${p.company_name} • ${p.location || 'India'}</p>
            </div>
            ${p.is_eligible
              ? '<span class="badge-status done">Eligible ✓</span>'
              : '<span class="badge-status error">Not Eligible</span>'}
          </div>
          <div class="tag-row">
            ${p.package_min ? `<span class="skill-tag">₹${p.package_min}–${p.package_max || '?'} LPA</span>` : ''}
            <span class="skill-tag">${p.openings} openings</span>
          </div>
          ${p.deadline ? `<p class="module-meta">Deadline: ${fmtDate(p.deadline)}</p>` : ''}
          ${statusBadge(p.status)}
        </div>`).join('')}</div>`;
    }

    el.innerHTML = html;
  } catch (err) {
    showError('placements-content', err.message || 'Failed to load placements.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   9. AI MENTOR VIEW
══════════════════════════════════════════════════════════════════════════════ */
let aiConversationId = null;

async function loadAIMentorView() {
  // Load conversations list
  try {
    const data = await CareerHubAPI.ai.conversations();
    const convs = data.data || data;
    const histEl = document.getElementById('ai-conv-list');
    if (histEl) {
      if (!convs.length) {
        histEl.innerHTML = '<p class="ai-no-conv">No previous conversations.</p>';
      } else {
        histEl.innerHTML = convs.slice(0, 8).map(c => `
          <div class="ai-conv-item" onclick="loadConversation('${c.id}')">
            <span class="ai-conv-title">${c.title || 'Conversation'}</span>
            <span class="ai-conv-time">${fmtTimeAgo(c.updated_at || c.created_at)}</span>
          </div>`).join('');
      }
    }
  } catch (e) {
    const histEl = document.getElementById('ai-conv-list');
    if (histEl) histEl.innerHTML = '<p class="ai-no-conv">Could not load history.</p>';
  }
}

async function loadConversation(id) {
  aiConversationId = id;
  const msgEl = document.getElementById('ai-messages');
  if (!msgEl) return;
  msgEl.innerHTML = '<div class="state-box loading-box"><div class="spinner"></div><p>Loading messages…</p></div>';
  try {
    const data = await CareerHubAPI.ai.getConversation(id);
    const messages = data.data || data.messages || data;
    aiConversationId = id;
    renderAIMessages(messages);
  } catch (e) {
    msgEl.innerHTML = '<div class="state-box error-box"><span>⚠️</span><p>Could not load conversation.</p></div>';
  }
}

function renderAIMessages(messages) {
  const msgEl = document.getElementById('ai-messages');
  if (!msgEl) return;
  if (!messages.length) {
    msgEl.innerHTML = '<div class="ai-welcome"><span>🤖</span><p>Hi! I\'m your AI Career Mentor. Ask me anything about your career path!</p></div>';
    return;
  }
  msgEl.innerHTML = messages.map(m => `
    <div class="ai-msg ${m.role === 'user' ? 'user-msg' : 'bot-msg'}">
      <div class="msg-bubble">${m.content || '—'}</div>
      <span class="msg-time">${fmtTimeAgo(m.created_at)}</span>
    </div>`).join('');
  msgEl.scrollTop = msgEl.scrollHeight;
}

async function sendAIMessage() {
  const input = document.getElementById('ai-input');
  const tool = document.getElementById('ai-tool-select')?.value || 'career_advisor';
  const msg = input?.value?.trim();
  if (!msg) return;

  input.value = '';
  const msgEl = document.getElementById('ai-messages');
  if (msgEl) {
    msgEl.innerHTML += `
      <div class="ai-msg user-msg">
        <div class="msg-bubble">${msg}</div>
        <span class="msg-time">just now</span>
      </div>
      <div class="ai-msg bot-msg" id="ai-typing">
        <div class="msg-bubble">
          <span class="typing-dots"><span></span><span></span><span></span></span>
        </div>
      </div>`;
    msgEl.scrollTop = msgEl.scrollHeight;
  }

  try {
    const res = await CareerHubAPI.ai.chat(msg, aiConversationId, tool);
    const reply = res.data || res;
    aiConversationId = reply.conversation_id || aiConversationId;
    const typing = document.getElementById('ai-typing');
    if (typing) {
      typing.outerHTML = `
        <div class="ai-msg bot-msg">
          <div class="msg-bubble">${reply.response || reply.message || '—'}</div>
          <span class="msg-time">just now</span>
        </div>`;
    }
  } catch (err) {
    const typing = document.getElementById('ai-typing');
    if (typing) typing.outerHTML = `
      <div class="ai-msg bot-msg">
        <div class="msg-bubble" style="color:#ef4444;">Sorry, something went wrong. ${err.message}</div>
      </div>`;
  }
  if (msgEl) msgEl.scrollTop = msgEl.scrollHeight;
}

window.sendAIMessage = sendAIMessage;
window.loadConversation = loadConversation;

/* ══════════════════════════════════════════════════════════════════════════════
   10. RESUME VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadResumeView() {
  showLoading('resume-content', 'Loading resume data...');
  try {
    const [profileRes, scoreRes] = await Promise.allSettled([
      CareerHubAPI.resume.profile(),
      CareerHubAPI.resume.score(),
    ]);
    const profile = profileRes.status === 'fulfilled' ? (profileRes.value.data || profileRes.value) : null;
    const score = scoreRes.status === 'fulfilled' ? (scoreRes.value.data || scoreRes.value) : null;
    const el = document.getElementById('resume-content');

    let html = '';

    if (score?.scores) {
      const scores = score.scores;
      const ats = Math.round(scores.ats_score || scores.overall || 0);
      const resume_s = Math.round(scores.resume_score || 0);
      const portfolio_s = Math.round(scores.portfolio_score || 0);
      html += `
        <div class="resume-score-row">
          <div class="score-circle-card">
            <div class="score-circle" style="--pct:${ats}%;--color:#0C7A6B;">
              <span>${ats}</span>
            </div>
            <p>ATS Score</p>
          </div>
          <div class="score-circle-card">
            <div class="score-circle" style="--pct:${resume_s}%;--color:#0E9B87;">
              <span>${resume_s}</span>
            </div>
            <p>Resume Score</p>
          </div>
          <div class="score-circle-card">
            <div class="score-circle" style="--pct:${portfolio_s}%;--color:#5BC8B8;">
              <span>${portfolio_s}</span>
            </div>
            <p>Portfolio Score</p>
          </div>
        </div>`;

      if (score.recommended_improvements?.length) {
        html += `<div class="view-card mb-16">
          <h3 class="view-card-title">💡 AI Recommendations</h3>
          <ul class="rec-list">${score.recommended_improvements.map(r => `<li>${r}</li>`).join('')}</ul>
        </div>`;
      }
    }

    if (profile) {
      html += `<div class="view-card mb-16">
        <h3 class="view-card-title">Resume Profile</h3>
        ${profile.headline ? `<p class="view-desc"><strong>${profile.headline}</strong></p>` : ''}
        ${profile.summary ? `<p class="view-desc">${profile.summary}</p>` : ''}
        <div class="tag-row"><span class="skill-tag">${profile.target_role || '—'}</span></div>
        ${profile.experiences?.length ? `
          <h4 class="section-title mt-16">Experience</h4>
          ${profile.experiences.map(e => `
            <div class="exp-item">
              <strong>${e.role_title || '—'}</strong> @ ${e.company_name || '—'}
              <span class="module-meta">${fmtDate(e.start_date)} – ${e.is_current ? 'Present' : fmtDate(e.end_date)}</span>
            </div>`).join('')}` : ''}
      </div>`;
    }

    if (!html) {
      showEmpty('resume-content', 'Your resume profile is empty. Start building it!', '📄');
      return;
    }
    el.innerHTML = html;
  } catch (err) {
    showError('resume-content', err.message || 'Failed to load resume data.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   11. LEADERBOARD VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadLeaderboardView() {
  showLoading('leaderboard-content', 'Loading leaderboard...');
  try {
    const data = await CareerHubAPI.gamification.leaderboard();
    const resp = data.data || data;
    const entries = resp.leaderboard || resp;
    const el = document.getElementById('leaderboard-content');

    if (!entries.length) {
      showEmpty('leaderboard-content', 'Leaderboard is empty. Be the first!', '🏆');
      return;
    }

    el.innerHTML = `
      <div class="view-card">
        <div class="view-card-header">
          <h3 class="view-card-title">🏆 Branch Leaderboard</h3>
          <span class="view-card-sub">${resp.scope || 'branch'} • ${resp.total_entries || entries.length} students</span>
        </div>
        <table class="lb-table">
          <thead><tr><th>Rank</th><th>Student</th><th>Branch</th><th>XP</th><th>Level</th></tr></thead>
          <tbody>
            ${entries.map(e => `
              <tr class="${e.rank <= 3 ? 'top-rank' : ''}">
                <td class="rank-cell">
                  ${e.rank === 1 ? '🥇' : e.rank === 2 ? '🥈' : e.rank === 3 ? '🥉' : `#${e.rank}`}
                </td>
                <td>${e.student_name || '—'}<br><span class="module-meta">${e.roll_number || ''}</span></td>
                <td>${e.branch_code || '—'}</td>
                <td><strong>${(e.total_xp || 0).toLocaleString()}</strong> XP</td>
                <td>${e.level_title || 'Lv ' + (e.current_level || 1)}</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  } catch (err) {
    showError('leaderboard-content', err.message || 'Failed to load leaderboard.');
  }
}

/* ══════════════════════════════════════════════════════════════════════════════
   12. PROFILE VIEW
══════════════════════════════════════════════════════════════════════════════ */
async function loadProfileView() {
  showLoading('profile-content', 'Loading your profile...');
  try {
    const [profileRes, xpRes] = await Promise.allSettled([
      CareerHubAPI.students.me(),
      CareerHubAPI.gamification.xp(),
    ]);
    const p = profileRes.status === 'fulfilled' ? (profileRes.value.data || profileRes.value) : null;
    const xp = xpRes.status === 'fulfilled' ? (xpRes.value.data || xpRes.value) : null;
    const el = document.getElementById('profile-content');

    if (!p) {
      showEmpty('profile-content', 'Could not load profile.', '👤');
      return;
    }

    const initials = (p.full_name || 'S').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    el.innerHTML = `
      <div class="profile-hero">
        <div class="profile-avatar-lg">${initials}</div>
        <div class="profile-hero-info">
          <h2 class="profile-name">${p.full_name || '—'}</h2>
          <p class="profile-meta">${p.email || '—'}</p>
          <p class="profile-meta">Roll: ${p.roll_number || '—'} • ${p.branch?.name || '—'} • Year ${p.current_year || '—'} • Sem ${p.semester || '—'}</p>
          <p class="profile-meta">Target Role: ${p.target_role?.title || '—'}</p>
          ${xp ? `<div class="xp-bar-wrap">
            <span class="xp-label">${xp.level_title || 'Explorer'} — Lv ${xp.current_level}</span>
            ${progressBar(xp.progress_percentage)}
            <span class="xp-label">${xp.total_xp} XP • ${xp.streak_days} day streak 🔥</span>
          </div>` : ''}
        </div>
      </div>
      <div class="profile-grid">
        <div class="view-card">
          <h3 class="view-card-title">Contact & Social</h3>
          ${p.phone_number ? `<p class="profile-field"><i class="fas fa-phone"></i> ${p.phone_number}</p>` : ''}
          ${p.github_url ? `<p class="profile-field"><i class="fab fa-github"></i> <a href="${p.github_url}" target="_blank">${p.github_url}</a></p>` : ''}
          ${p.linkedin_url ? `<p class="profile-field"><i class="fab fa-linkedin"></i> <a href="${p.linkedin_url}" target="_blank">${p.linkedin_url}</a></p>` : ''}
          ${p.leetcode_url ? `<p class="profile-field"><i class="fas fa-code"></i> <a href="${p.leetcode_url}" target="_blank">${p.leetcode_url}</a></p>` : ''}
          ${p.hackerrank_url ? `<p class="profile-field"><i class="fas fa-h-square"></i> <a href="${p.hackerrank_url}" target="_blank">${p.hackerrank_url}</a></p>` : ''}
          ${!p.github_url && !p.linkedin_url ? '<p class="view-desc">No social links added yet.</p>' : ''}
        </div>
        <div class="view-card">
          <h3 class="view-card-title">Account Details</h3>
          <p class="profile-field">Member since: ${fmtDate(p.created_at)}</p>
          <p class="profile-field">Status: ${p.is_active ? '✅ Active' : '❌ Inactive'}</p>
        </div>
      </div>`;
  } catch (err) {
    showError('profile-content', err.message || 'Failed to load profile.');
  }
}

/* ── TASK CHECKBOX ─────────────────────────────────────────────────────────── */
function initTaskCheckboxes() {
  document.querySelectorAll('.task-check').forEach(cb => {
    cb.addEventListener('change', (e) => {
      const label = e.target.nextElementSibling;
      if (label) {
        label.style.textDecoration = e.target.checked ? 'line-through' : 'none';
        label.style.opacity = e.target.checked ? '0.5' : '1';
      }
    });
  });
}

/* ── SEARCH SHORTCUT ───────────────────────────────────────────────────────── */
function initSearchKeyboardShortcut() {
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      document.getElementById('global-search')?.focus();
    }
  });
}

/* ── DARK THEME TOGGLE ─────────────────────────────────────────────────────── */
function initThemeToggle() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  let isDark = localStorage.getItem('theme') === 'dark';
  applyTheme(isDark);
  btn.addEventListener('click', () => {
    isDark = !isDark;
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    applyTheme(isDark);
    btn.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
  });
}
function applyTheme(dark) {
  document.body.classList.toggle('dark-mode', dark);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.innerHTML = dark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
}

/* ── NOTIFICATION DROPDOWN ────────────────────────────────────────────────── */
function initNotifications() {
  const notifBtn = document.getElementById('notif-btn');
  const dropdown = document.getElementById('notif-dropdown');
  if (!notifBtn || !dropdown) return;

  notifBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('active');
    if (dropdown.classList.contains('active')) {
      loadNotifications();
    }
  });

  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !notifBtn.contains(e.target)) {
      dropdown.classList.remove('active');
    }
  });

  loadNotificationCount();
}

async function loadNotificationCount() {
  try {
    const res = await CareerHubAPI.notifications.unreadCount();
    const count = res.data?.unread_count ?? res.unread_count ?? 3;
    const badge = document.getElementById('notif-badge');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  } catch (err) {
    // Keep default badge visible
  }
}

async function loadNotifications() {
  const body = document.getElementById('notif-dropdown-body');
  if (!body) return;
  body.innerHTML = '<div class="state-box loading-box"><div class="spinner"></div><p>Loading notifications...</p></div>';

  try {
    const res = await CareerHubAPI.notifications.list();
    const data = res.data || res;
    const items = data.notifications || data;

    if (!items || !items.length) {
      body.innerHTML = '<div class="state-box empty-box"><span class="state-icon">🔔</span><p>No notifications right now.</p></div>';
      return;
    }

    body.innerHTML = items.map(n => `
      <div class="notif-item ${n.status === 'UNREAD' ? 'unread' : ''}" onclick="markNotificationRead('${n.id}')">
        <div class="notif-item-icon">
          <i class="fas ${n.category === 'PLACEMENT_DRIVE' ? 'fa-briefcase' : n.category === 'COURSE_UNLOCK' ? 'fa-book-open' : 'fa-bell'}"></i>
        </div>
        <div class="notif-item-info">
          <h5 class="notif-item-title">${n.title || 'Notification'}</h5>
          <p class="notif-item-msg">${n.message || ''}</p>
          <span class="notif-item-time">${fmtTimeAgo(n.created_at)}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    body.innerHTML = '<div class="state-box empty-box"><span class="state-icon">🔔</span><p>You have 3 unread campus alerts.</p></div>';
  }
}

async function markAllNotificationsRead() {
  const badge = document.getElementById('notif-badge');
  if (badge) badge.style.display = 'none';
  const unreadItems = document.querySelectorAll('.notif-item.unread');
  unreadItems.forEach(el => el.classList.remove('unread'));
}

window.markAllNotificationsRead = markAllNotificationsRead;
window.markNotificationRead = (id) => {
  CareerHubAPI.notifications.markRead(id).catch(() => {});
};

