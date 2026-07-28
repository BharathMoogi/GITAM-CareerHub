/* ==========================================================================
   GITAM CareerHub — Interactive Landing Page JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initCareerJourney();
  initRoadmaps();
  initCompaniesFilter();
  initReadinessCalculator();
  initFAQAccordion();

  initSmoothScroll();
});

/* 1. Navbar Scroll Effect & Active Link Highlight */
function initNavbar() {
  const navbar = document.querySelector('.navbar');
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('section[id]');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }

    // Active Section Highlight
    let current = '';
    sections.forEach(section => {
      const sectionTop = section.offsetTop - 120;
      const sectionHeight = section.offsetHeight;
      if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
        current = section.getAttribute('id');
      }
    });

    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  });
}

/* 2. Career Journey Year-by-Year Interactive Switcher */
function initCareerJourney() {
  const journeyData = {
    y1: {
      badge: "Year 1 • Foundation & Exploration",
      title: "Discover Your Engineering Track",
      desc: "Explore core engineering fundamentals, master Python & C++, construct your first GitHub repository, and choose your specialization track.",
      checklist: [
        "Core Programming & Data Structures Fundamentals",
        "Git & Open Source Contribution Setup",
        "Career Mentor Mapping & Skill Baseline Assessment",
        "Participation in 24-hr Freshman Hackathons"
      ],
      xp: "+500 XP",
      level: "Level 1: Explorer"
    },
    y2: {
      badge: "Year 2 • Building & Specialization",
      title: "Core Specialization & Project Building",
      desc: "Deep dive into your selected branch (AI/ML, Embedded Systems, VLSI, Robotics, or Cloud/Software). Build end-to-end industry projects.",
      checklist: [
        "Branch-specific Advanced Skill Modules",
        "Completion of 3 Industry Capstone Projects",
        "Global Certification Preparation (AWS / NVIDIA / Arm)",
        "Resume V1.0 Generation & Portfolio Hosting"
      ],
      xp: "+1,200 XP",
      level: "Level 3: Builder"
    },
    y3: {
      badge: "Year 3 • Industry Alignment & Internships",
      title: "Industry Projects & Summer Internships",
      desc: "Apply for top tier company internships, complete mock interviews with AI Mentor, master system design, and earn verified credentials.",
      checklist: [
        "5-Stage Internship Drive Participation",
        "System Design & Algorithmic Interview Preparation",
        "Live Industry Mentorship & Portfolio Reviews",
        "Summer Internship Placement at Tier-1 Companies"
      ],
      xp: "+2,500 XP",
      level: "Level 5: Professional"
    },
    y4: {
      badge: "Year 4 • Placement Command & Leadership",
      title: "Campus Placements & Dream Offers",
      desc: "Unlock premium campus recruitment drives (20 LPA+ dream companies), negotiate multi-offers, and achieve 100% career readiness.",
      checklist: [
        "Direct Placement Drive Applications for 50+ Top Tech Companies",
        "Final Year Major Industry Project Defense",
        "Mock HR & Technical Leadership Interviews",
        "Multiple High-Package Offer Letter Finalization"
      ],
      xp: "+5,000 XP",
      level: "Level 6: Industry Ready"
    }
  };

  const tabs = document.querySelectorAll('.journey-tab');
  const badgeEl = document.getElementById('journey-badge');
  const titleEl = document.getElementById('journey-title');
  const descEl = document.getElementById('journey-desc');
  const checklistEl = document.getElementById('journey-checklist');
  const levelEl = document.getElementById('journey-level');
  const xpEl = document.getElementById('journey-xp');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const yearKey = tab.dataset.year;
      const data = journeyData[yearKey];

      if (data) {
        badgeEl.textContent = data.badge;
        titleEl.textContent = data.title;
        descEl.textContent = data.desc;
        levelEl.textContent = data.level;
        xpEl.textContent = data.xp;

        checklistEl.innerHTML = data.checklist.map(item => `
          <li><i class="fas fa-check-circle"></i> <span>${item}</span></li>
        `).join('');
      }
    });
  });
}

/* 3. Engineering Roadmaps Tab Switcher */
function initRoadmaps() {
  const roadmapData = {
    all: [
      { title: "AI & Machine Learning", branch: "AIML / CSE", semesters: "Semesters 1 - 8", icon: "fa-brain", certs: "NVIDIA Deep Learning Institute, TensorFlow Developer", salary: "18 - 45 LPA" },
      { title: "Embedded Systems & IoT", branch: "ECE / EEE", semesters: "Semesters 1 - 8", icon: "fa-microchip", certs: "Arm Microcontroller Architect, STMicroelectronics Specialist", salary: "14 - 32 LPA" },
      { title: "Robotics & Automation", branch: "MECH / ECE", semesters: "Semesters 1 - 8", icon: "fa-robot", certs: "ROS2 Robotics Developer, MATLAB Robotics System", salary: "12 - 28 LPA" },
      { title: "VLSI & Semiconductor Design", branch: "ECE / VLSI", semesters: "Semesters 1 - 8", icon: "fa-memory", certs: "Cadence Design Systems, Synopsys Chip Architect", salary: "20 - 50 LPA" },
      { title: "Software & Cloud Engineering", branch: "CSE / IT", semesters: "Semesters 1 - 8", icon: "fa-code", certs: "AWS Solutions Architect, Google Cloud Professional", salary: "16 - 42 LPA" }
    ],
    software: [
      { title: "Software & Cloud Engineering", branch: "CSE / IT", semesters: "Semesters 1 - 8", icon: "fa-code", certs: "AWS Solutions Architect, Google Cloud Professional", salary: "16 - 42 LPA" }
    ],
    hardware: [
      { title: "Embedded Systems & IoT", branch: "ECE / EEE", semesters: "Semesters 1 - 8", icon: "fa-microchip", certs: "Arm Microcontroller Architect, STMicroelectronics Specialist", salary: "14 - 32 LPA" },
      { title: "VLSI & Semiconductor Design", branch: "ECE / VLSI", semesters: "Semesters 1 - 8", icon: "fa-memory", certs: "Cadence Design Systems, Synopsys Chip Architect", salary: "20 - 50 LPA" }
    ],
    ai: [
      { title: "AI & Machine Learning", branch: "AIML / CSE", semesters: "Semesters 1 - 8", icon: "fa-brain", certs: "NVIDIA Deep Learning Institute, TensorFlow Developer", salary: "18 - 45 LPA" }
    ],
    robotics: [
      { title: "Robotics & Automation", branch: "MECH / ECE", semesters: "Semesters 1 - 8", icon: "fa-robot", certs: "ROS2 Robotics Developer, MATLAB Robotics System", salary: "12 - 28 LPA" }
    ]
  };

  const navBtns = document.querySelectorAll('.roadmap-nav-btn');
  const grid = document.getElementById('roadmap-grid');

  function renderCards(category) {
    const cards = roadmapData[category] || roadmapData.all;
    grid.innerHTML = cards.map(c => `
      <div class="roadmap-card">
        <div class="roadmap-header">
          <div class="roadmap-icon"><i class="fas ${c.icon}"></i></div>
          <span class="roadmap-semesters">${c.semesters}</span>
        </div>
        <h3 style="font-size: 1.25rem; margin-bottom: 8px;">${c.title}</h3>
        <p style="color: var(--color-text-muted); font-size: 0.9rem; margin-bottom: 16px;">Target Branch: <strong style="color: white;">${c.branch}</strong></p>
        <div style="padding-top: 16px; border-top: 1px solid var(--color-card-border);">
          <div style="font-size: 0.85rem; color: var(--color-text-subtle); margin-bottom: 6px;">Top Certifications:</div>
          <div style="font-size: 0.9rem; color: var(--color-gitam-gold); font-weight: 600;">${c.certs}</div>
          <div style="margin-top: 12px; font-size: 0.85rem; color: #34D399; font-weight: 700;">Avg Package: ${c.salary}</div>
        </div>
      </div>
    `).join('');
  }

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      navBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderCards(btn.dataset.category);
    });
  });

  renderCards('all');
}

/* 4. Company Category Filter */
function initCompaniesFilter() {
  const companies = [
    { name: "Google", ctc: "45.0 LPA", cat: "product", icon: "fab fa-google" },
    { name: "Microsoft", ctc: "43.5 LPA", cat: "product", icon: "fab fa-microsoft" },
    { name: "Amazon", ctc: "44.0 LPA", cat: "product", icon: "fab fa-amazon" },
    { name: "Bosch", ctc: "16.0 LPA", cat: "core", icon: "fas fa-microchip" },
    { name: "Texas Instruments", ctc: "26.0 LPA", cat: "core", icon: "fas fa-memory" },
    { name: "NVIDIA", ctc: "38.0 LPA", cat: "ai", icon: "fas fa-brain" },
    { name: "Qualcomm", ctc: "22.5 LPA", cat: "hardware", icon: "fas fa-wifi" },
    { name: "Oracle", ctc: "32.0 LPA", cat: "product", icon: "fas fa-database" },
    { name: "Intel", ctc: "24.0 LPA", cat: "hardware", icon: "fas fa-laptop-code" },
    { name: "Salesforce", ctc: "36.0 LPA", cat: "product", icon: "fas fa-cloud" },
    { name: "Schneider Electric", ctc: "14.5 LPA", cat: "core", icon: "fas fa-bolt" },
    { name: "Siemens", ctc: "15.0 LPA", cat: "core", icon: "fas fa-cogs" }
  ];

  const grid = document.getElementById('company-grid');
  if (!grid) return;

  grid.innerHTML = companies.map(c => `
    <div class="company-box">
      <div class="company-icon"><i class="${c.icon}"></i></div>
      <div class="company-name">${c.name}</div>
      <div class="company-ctc">${c.ctc}</div>
    </div>
  `).join('');
}

/* 5. Interactive Career Readiness Score Calculator */
function initReadinessCalculator() {
  const yearSelect = document.getElementById('calc-year');
  const branchSelect = document.getElementById('calc-branch');
  const projectsInput = document.getElementById('calc-projects');
  const certsInput = document.getElementById('calc-certs');
  const scoreNum = document.getElementById('calc-score');
  const levelText = document.getElementById('calc-level');
  const barInner = document.getElementById('calc-bar');

  function calculateScore() {
    const year = parseInt(yearSelect.value) || 1;
    const projects = parseInt(projectsInput.value) || 0;
    const certs = parseInt(certsInput.value) || 0;

    // Calculation algorithm
    let baseScore = year * 15;
    let projectPoints = Math.min(projects * 12, 36);
    let certPoints = Math.min(certs * 10, 20);

    let totalScore = Math.min(baseScore + projectPoints + certPoints, 98);

    scoreNum.textContent = totalScore;
    if (barInner) barInner.style.width = `${totalScore}%`;

    if (totalScore >= 80) {
      levelText.textContent = "Placement Ready (Tier-1 Ready)";
      levelText.style.color = "#34D399";
    } else if (totalScore >= 55) {
      levelText.textContent = "Intermediate Builder";
      levelText.style.color = "#E5A93C";
    } else {
      levelText.textContent = "Career Explorer";
      levelText.style.color = "#60A5FA";
    }
  }

  [yearSelect, branchSelect, projectsInput, certsInput].forEach(el => {
    if (el) el.addEventListener('change', calculateScore);
    if (el) el.addEventListener('input', calculateScore);
  });

  calculateScore();
}

/* 6. FAQ Accordion Toggle */
function initFAQAccordion() {
  const items = document.querySelectorAll('.faq-item');
  items.forEach(item => {
    const question = item.querySelector('.faq-question');
    question.addEventListener('click', () => {
      const isActive = item.classList.contains('active');
      items.forEach(i => i.classList.remove('active'));
      if (!isActive) {
        item.classList.add('active');
      }
    });
  });
}


/* 8. Smooth Scrolling */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({
          behavior: 'smooth'
        });
      }
    });
  });
}
