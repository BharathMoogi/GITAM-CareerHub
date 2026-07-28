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

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    submitBtn.textContent = 'LOGGING IN...';
    submitBtn.disabled = true;

    // Save mock user session and redirect immediately to Student Dashboard
    localStorage.setItem('user_logged_in', 'true');
    localStorage.setItem('user_name', 'Bharath M');
    localStorage.setItem('user_role', currentRole);

    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 200);
  });
}
