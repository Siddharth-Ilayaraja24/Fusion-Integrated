export interface Page<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Department {
  id: number;
  code: string;
  name: string;
  description: string;
  contact_email: string;
  location: string;
  website_url: string;
  core_policies: string;
  active_hod_user_id: number | null;
  active_dept_admin_user_id: number | null;
  updated_at: string;
}

export interface OfficialDetailChange {
  id: number;
  department_id: number;
  field_name: string;
  previous_value: string;
  proposed_value: string;
  status: string;
  proposed_by_user_id: number;
  decided_by_user_id: number | null;
  decided_at: string | null;
  decision_note: string;
  created_at: string;
}

export interface Announcement {
  id: number;
  department_id: number;
  title: string;
  content: string;
  target_roles: string[];
  target_programs: string[];
  target_academic_years: string[];
  status: string;
  created_by_user_id: number;
  updated_by_user_id: number | null;
  created_at: string;
}

export interface InventoryItem {
  id: number;
  department_id: number;
  sku: string;
  name: string;
  category: string;
  unit: string;
  current_quantity: number;
  location: string;
  description: string;
  updated_at: string;
}

export interface StockRequest {
  id: number;
  department_id: number;
  item_id: number;
  item_name: string;
  item_sku: string;
  requester_user_id: number;
  requested_quantity: number;
  purpose: string;
  status: string;
  hod_decided_by_user_id: number | null;
  hod_decided_at: string | null;
  hod_note: string;
  issued_by_user_id: number | null;
  issued_at: string | null;
  created_at: string;
}

export interface StockMovement {
  id: number;
  department_id: number;
  item_id: number;
  item_sku: string;
  item_name: string;
  stock_request_id: number | null;
  movement_type: string;
  quantity_delta: number;
  balance_after: number;
  actor_user_id: number;
  note: string;
  created_at: string;
}

export interface Feedback {
  id: number;
  department_id: number;
  submitter_user_id: number;
  submitter_role: string;
  subject: string;
  body: string;
  category: string;
  status: string;
  initial_reviewed_by_user_id: number | null;
  initial_reviewed_at: string | null;
  resolved_by_user_id: number | null;
  resolved_at: string | null;
  resolution_note: string;
  created_at: string;
}

export interface TimetableSlot {
  id: number;
  department_id: number;
  slot_kind: string;
  program: string;
  academic_year: string;
  section: string;
  course_code: string;
  course_title: string;
  faculty_user_id: number | null;
  room: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export interface LabResource {
  id: number;
  department_id: number;
  lab_code: string;
  name: string;
  location: string;
  equipment_summary: string;
  capacity: number;
  status: string;
  incharge_user_id: number | null;
  updated_at: string;
}

export interface DepartmentProgram {
  id: number;
  department_id: number;
  code: string;
  name: string;
  degree_level: string;
  duration_years: number;
  description: string;
  is_active: boolean;
}

export interface DepartmentProfile {
  id: number;
  department_id: number;
  user_id: number;
  profile_kind: string;
  display_name: string;
  program: string;
  visibility_tier: string;
  email?: string;
  academic_year?: string;
  designation_title?: string;
  office_room?: string;
  research_area?: string;
  graduation_year?: number | null;
  current_affiliation?: string;
  academic_notes?: string;
}

export interface RoleAssignment {
  id: number;
  department_id: number;
  role_type: string;
  user_id: number;
  valid_from: string;
  valid_to: string;
  status: string;
  assigned_by_user_id: number;
  activated_at: string | null;
  revoked_at: string | null;
  created_at: string;
}
