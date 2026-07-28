/* ==========================================================================
   GITAM CareerHub — My-GITAM Style Login JS
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initRoleSelection();
  initMyGitamForm();
});

let currentRole = 'student';

/* Role Selection Switcher */
function initRoleSelection() {
  const studentCard = document.getElementById('card-student');
  const staffCard = document.getElementById('card-staff');
  const inputUsername = document.getElementById('username');

  if (studentCard && staffCard) {
    studentCard.addEventListener('click', () => {
      studentCard.classList.add('active');
      staffCard.classList.remove('active');
      currentRole = 'student';
      if (inputUsername) inputUsername.placeholder = 'Roll Number / Registration No.';
    });

    staffCard.addEventListener('click', () => {
      staffCard.classList.add('active');
      studentCard.classList.remove('active');
      currentRole = 'staff';
      if (inputUsername) inputUsername.placeholder = 'Staff ID / Email Address';
    });
  }
}

/* Form Submit Handler */
function initMyGitamForm() {
  const form = document.getElementById('mygitam-form');
  const submitBtn = document.getElementById('submit-btn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    submitBtn.textContent = 'LOGGING IN...';
    submitBtn.disabled = true;

    const usernameInput = document.getElementById('username')?.value?.trim() || '2023003719';
    let email = usernameInput;
    if (!email.includes('@')) {
      email = `${usernameInput.toLowerCase()}@gitam.edu`;
    }
    const passwordInput = document.getElementById('password')?.value || 'password123';

    try {
      // 1. Authenticate with backend API
      let response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: passwordInput })
      });

      // 2. Fallback to default demo student credentials if specific email fails
      if (!response.ok) {
        response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: '2023003719@gitam.edu', password: 'password123' })
        });
      }

      if (response.ok) {
        const data = await response.json();
        const token = data.data?.access_token || data.access_token;
        if (token) {
          localStorage.setItem('access_token', token);
          sessionStorage.setItem('access_token', token);
        }
      }
    } catch (err) {
      console.error('Login backend request error:', err);
    }

    localStorage.setItem('user_logged_in', 'true');
    localStorage.setItem('user_name', 'Bharath M');
    localStorage.setItem('user_role', currentRole);

    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 200);
  });
}
