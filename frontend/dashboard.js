/* ==========================================================================
   GITAM CareerHub — Student Dashboard Interactive JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initSidebarNav();
  initTaskCheckboxes();
  initSearchKeyboardShortcut();
  initThemeToggle();
  initAIRecommendationBtn();
});

/* 1. Sidebar Navigation Switcher */
function initSidebarNav() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const page = item.getAttribute('data-page');
      console.log(`Switched view to: ${page}`);
    });
  });
}

/* 2. Today's Tasks Checkbox Handler */
function initTaskCheckboxes() {
  const checkboxes = document.querySelectorAll('.task-check');
  checkboxes.forEach(cb => {
    cb.addEventListener('change', (e) => {
      const label = e.target.nextElementSibling;
      if (e.target.checked) {
        label.style.textDecoration = 'line-through';
        label.style.opacity = '0.5';
      } else {
        label.style.textDecoration = 'none';
        label.style.opacity = '1';
      }
    });
  });
}

/* 3. Global Search Keyboard Shortcut (Cmd/Ctrl + K) */
function initSearchKeyboardShortcut() {
  const searchInput = document.getElementById('global-search');
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (searchInput) {
        searchInput.focus();
      }
    }
  });
}

/* 4. Dark Theme Toggle */
function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  let isDark = false;
  
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      isDark = !isDark;
      if (isDark) {
        document.body.style.backgroundColor = '#0F172A';
        document.body.style.color = '#F8FAFC';
        toggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
      } else {
        document.body.style.backgroundColor = '#F4F7F6';
        document.body.style.color = '#1E293B';
        toggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
      }
    });
  }
}

/* 5. AI Recommendation Start Button */
function initAIRecommendationBtn() {
  const btn = document.getElementById('ai-start-btn');
  if (btn) {
    btn.addEventListener('click', () => {
      alert('Launching RTOS Embedded Systems Interactive Module...');
    });
  }
}
