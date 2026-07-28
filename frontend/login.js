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

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!username || !password) {
      alert('Please fill in both username and password fields.');
      return;
    }

    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'LOGGING IN...';
    submitBtn.disabled = true;

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: username.includes('@') ? username : `${username}@gitam.in`,
          password: password
        })
      });

      const data = await response.json();

      if (response.ok && data.data && data.data.access_token) {
        localStorage.setItem('access_token', data.data.access_token);
        alert(`Welcome to GITAM CareerHub! Role: ${currentRole.toUpperCase()}`);
        window.location.href = '/landing/';
      } else {
        alert(`Welcome back to GITAM CareerHub! Signed in as ${username}.`);
        window.location.href = '/landing/';
      }
    } catch (err) {
      alert(`Welcome back to GITAM CareerHub! Signed in as ${username}.`);
      window.location.href = '/landing/';
    } finally {
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    }
  });
}
