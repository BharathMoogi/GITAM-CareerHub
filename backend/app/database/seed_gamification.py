"""
Seed data for the Career Gamification Engine.

Includes:
  - 6 Levels (Level 1 Explorer to Level 6 Industry Ready)
  - 11 Achievements (First Course, First Project, First Certification, etc.)
  - Badges (Bronze to Diamond tiers)
  - Daily, Weekly, and Monthly Challenges
  - Unlockable Rewards
"""
from datetime import date, timedelta

LEVELS_SEED = [
    {"level_number": 1, "title": "Explorer", "min_xp": 0},
    {"level_number": 2, "title": "Learner", "min_xp": 300},
    {"level_number": 3, "title": "Builder", "min_xp": 750},
    {"level_number": 4, "title": "Engineer", "min_xp": 1500},
    {"level_number": 5, "title": "Professional", "min_xp": 3000},
    {"level_number": 6, "title": "Industry Ready", "min_xp": 5000},
]

ACHIEVEMENTS_SEED = [
    {"code": "FIRST_COURSE", "title": "First Course", "description": "Complete your first course on GITAM CareerHub", "xp_reward": 100, "category": "ACADEMIC"},
    {"code": "FIRST_PROJECT", "title": "First Project", "description": "Successfully submit your first practical project", "xp_reward": 250, "category": "PROJECT"},
    {"code": "FIRST_CERT", "title": "First Certification", "description": "Earn your first verified academic or industry certification", "xp_reward": 300, "category": "CERTIFICATION"},
    {"code": "FIRST_INTERNSHIP", "title": "First Internship", "description": "Secure your first internship offer through CareerHub", "xp_reward": 600, "category": "PLACEMENT"},
    {"code": "100_HOURS", "title": "100 Hours Learning", "description": "Accumulate 100 total hours of structured learning and project building", "xp_reward": 500, "category": "ACADEMIC"},
    {"code": "TOP_10_RANK", "title": "Top 10 Rank", "description": "Achieve a Top 10 rank on the Department or College Leaderboard", "xp_reward": 400, "category": "LEADERBOARD"},
    {"code": "BOSCH_READY", "title": "Bosch Ready", "description": "Achieve >=70% readiness score for Bosch India", "xp_reward": 300, "category": "READINESS"},
    {"code": "GOOGLE_READY", "title": "Google Ready", "description": "Achieve >=70% readiness score for Google India", "xp_reward": 500, "category": "READINESS"},
    {"code": "INTERVIEW_READY", "title": "Interview Ready", "description": "Complete 5 mock interview modules with high evaluation scores", "xp_reward": 350, "category": "INTERVIEW"},
    {"code": "RESUME_COMPLETE", "title": "Resume Complete", "description": "Build an ATS-optimized resume with >=80% resume score", "xp_reward": 150, "category": "PROFILE"},
    {"code": "PORTFOLIO_COMPLETE", "title": "Portfolio Complete", "description": "Connect GitHub and feature at least 3 completed projects", "xp_reward": 200, "category": "PROFILE"},
]

BADGES_SEED = [
    {"code": "BADGE_FIRST_STEP", "name": "First Step", "description": "Completed first course", "tier": "BRONZE", "category": "ACADEMIC"},
    {"code": "BADGE_CODE_MASTER", "name": "Code Master", "description": "Submitted 3+ technical projects", "tier": "SILVER", "category": "PROJECT"},
    {"code": "BADGE_CERTIFIED_PRO", "name": "Certified Professional", "description": "Earned 3+ industry certifications", "tier": "GOLD", "category": "CERTIFICATION"},
    {"code": "BADGE_INDUSTRY_STAR", "name": "Industry Star", "description": "Achieved Level 6 Industry Ready status", "tier": "PLATINUM", "category": "READINESS"},
    {"code": "BADGE_TOP_PERFORMER", "name": "Top Performer", "description": "Ranked #1 in Department Leaderboard", "tier": "DIAMOND", "category": "LEADERBOARD"},
]

DAILY_CHALLENGES_SEED = [
    {"title": "Daily Learning Habit", "description": "Complete 30 minutes of course learning today", "xp_reward": 50, "category": "DAILY"},
    {"title": "AI Mentor Check-in", "description": "Ask the AI Career Advisor for feedback on your progress", "xp_reward": 30, "category": "DAILY"},
    {"title": "LeetCode Practice", "description": "Solve 1 LeetCode or DSA problem", "xp_reward": 40, "category": "DAILY"},
]

WEEKLY_CHALLENGES_SEED = [
    {"title": "Weekly Module Sprint", "description": "Complete 1 full Roadmap Module this week", "xp_reward": 150, "category": "WEEKLY"},
    {"title": "Project Milestone", "description": "Submit code or deliverable for an active project", "xp_reward": 200, "category": "WEEKLY"},
]

MONTHLY_CHALLENGES_SEED = [
    {"title": "Monthly Certification Goal", "description": "Complete 1 NPTEL or Vendor Certification this month", "xp_reward": 400, "category": "MONTHLY"},
    {"title": "Company Readiness Target", "description": "Increase overall readiness score for target company by 10 points", "xp_reward": 500, "category": "MONTHLY"},
]

REWARDS_SEED = [
    {"title": "Resume Review Voucher", "description": "Get a 1-on-1 expert human resume review by GITAM Placement Cell", "min_level_required": 2, "xp_cost": 200, "reward_type": "VOUCHER"},
    {"title": "Mock Interview Pass", "description": "Priority access to 1-on-1 mock technical interviews with alumni", "min_level_required": 3, "xp_cost": 400, "reward_type": "VOUCHER"},
    {"title": "Company Referral Priority", "description": "Get priority referral consideration for partner company drives", "min_level_required": 4, "xp_cost": 800, "reward_type": "REFERRAL"},
    {"title": "Golden Profile Badge Frame", "description": "Exclusive golden frame around your avatar on Leaderboards", "min_level_required": 5, "xp_cost": 1000, "reward_type": "BADGE_FRAME"},
]
