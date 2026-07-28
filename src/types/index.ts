/* ==========================================================================
   GITAM CareerHub — Type Definitions for API Layer & FastAPI Backend
   ========================================================================== */

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  meta?: Record<string, any>;
}

export interface UserTokenData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface StudentProfile {
  id: string;
  roll_number: string;
  first_name: string;
  last_name: string;
  email: string;
  branch: string;
  year: number;
  semester: number;
  cgpa: number;
  target_role: string;
  target_company?: string;
  profile_picture?: string;
}

export interface DashboardSummary {
  career_readiness: {
    score: number;
    grade: string;
    description: string;
  };
  roadmap_progress: {
    percentage: number;
    status: string;
    completed_milestones: number;
    total_milestones: number;
  };
  projects_completed: {
    completed: number;
    total: number;
    status_message: string;
  };
  certificates_earned: {
    earned: number;
    total: number;
    status_message: string;
  };
  applications: {
    total_applied: number;
    in_review: number;
    shortlisted: number;
  };
  offers_received: {
    count: number;
    message: string;
  };
  streak: {
    days: number;
    message: string;
  };
  tasks: Array<{
    id: string;
    title: string;
    category: 'Course' | 'Project' | 'Internship' | 'Interview';
    due_label: string;
    is_completed: boolean;
  }>;
  ai_recommendation: {
    title: string;
    description: string;
    action_url?: string;
  };
  upcoming_deadlines: Array<{
    id: string;
    title: string;
    date: string;
    urgency: 'urgent' | 'warning' | 'normal';
  }>;
  top_companies: Array<{
    id: string;
    name: string;
    match_percentage: number;
    logo_letter: string;
    logo_color: string;
  }>;
  skill_distribution: {
    overall_score: number;
    skills: Array<{
      name: string;
      percentage: number;
      color: string;
    }>;
  };
  weekly_progress: {
    period: string;
    labels: string[];
    data: number[];
  };
  recent_activity: Array<{
    id: string;
    type: 'course' | 'project' | 'cert' | 'apply';
    title: string;
    timestamp: string;
  }>;
}

export interface RoadmapItem {
  id: string;
  branch: string;
  year: number;
  semester: number;
  title: string;
  category: string;
  description: string;
  is_completed: boolean;
  skills: string[];
}

export interface Course {
  id: string;
  title: string;
  provider: string;
  duration_weeks: number;
  level: string;
  branch: string;
  enrolled: boolean;
  progress_percentage: number;
}

export interface Project {
  id: string;
  title: string;
  branch: string;
  difficulty: string;
  tech_stack: string[];
  description: string;
  status: 'not_started' | 'in_progress' | 'completed';
}

export interface Certification {
  id: string;
  name: string;
  issuer: string;
  credential_url?: string;
  earned_date?: string;
  status: 'earned' | 'in_progress' | 'recommended';
}

export interface Company {
  id: string;
  name: string;
  industry: string;
  min_cgpa: number;
  hiring_roles: string[];
  match_percentage: number;
}

export interface Internship {
  id: string;
  title: string;
  company_name: string;
  stipend: string;
  location: string;
  deadline: string;
  status: 'open' | 'applied' | 'closed';
}

export interface PlacementDrive {
  id: string;
  company_name: string;
  role: string;
  ctc_lpa: number;
  visit_date: string;
  eligible_branches: string[];
  status: 'upcoming' | 'ongoing' | 'completed';
}

export interface AIChatMessage {
  id: string;
  sender: 'user' | 'ai';
  message: string;
  timestamp: string;
}
