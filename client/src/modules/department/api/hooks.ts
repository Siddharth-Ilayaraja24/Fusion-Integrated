import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { http } from "../../../lib/http";
import type {
  Announcement,
  Department,
  DepartmentProfile,
  DepartmentProgram,
  Feedback,
  InventoryItem,
  LabResource,
  OfficialDetailChange,
  Page,
  RoleAssignment,
  StockMovement,
  StockRequest,
  TimetableSlot,
} from "./types";

const KEY = "department";

export const keys = {
  departments: () => [KEY, "departments"] as const,
  officialChanges: () => [KEY, "official-changes"] as const,
  announcements: () => [KEY, "announcements"] as const,
  inventory: () => [KEY, "inventory"] as const,
  stockRequests: () => [KEY, "stock-requests"] as const,
  stockMovements: () => [KEY, "stock-movements"] as const,
  feedback: () => [KEY, "feedback"] as const,
  timetables: () => [KEY, "timetables"] as const,
  labs: () => [KEY, "labs"] as const,
  programs: () => [KEY, "programs"] as const,
  profiles: () => [KEY, "profiles"] as const,
  roleAssignments: () => [KEY, "role-assignments"] as const,
};

function invalidateAll(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: [KEY] });
}

export function useDepartments() {
  return useQuery({
    queryKey: keys.departments(),
    queryFn: async () => (await http.get<Page<Department>>("/department/departments")).data,
  });
}

export function useUpdateDepartment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (arg: { id: number; description?: string; location?: string }) =>
      (await http.patch<Department>(`/department/departments/${arg.id}`, arg)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useOfficialChanges(enabled = true) {
  return useQuery({
    queryKey: keys.officialChanges(),
    queryFn: async () =>
      (await http.get<Page<OfficialDetailChange>>("/department/official-changes")).data,
    enabled,
  });
}

export function useProposeOfficialChange() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      department_id: number;
      field_name: string;
      proposed_value: string;
    }) => (await http.post<OfficialDetailChange>("/department/official-changes", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDecideOfficialChange() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (arg: { id: number; approve: boolean; note?: string }) =>
      (
        await http.post<OfficialDetailChange>(`/department/official-changes/${arg.id}/decide`, {
          approve: arg.approve,
          note: arg.note ?? "",
        })
      ).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useAnnouncements() {
  return useQuery({
    queryKey: keys.announcements(),
    queryFn: async () => (await http.get<Page<Announcement>>("/department/announcements")).data,
  });
}

export function useCreateAnnouncement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      department_id: number;
      title: string;
      content: string;
      target_roles: string[];
      target_programs?: string[];
      target_academic_years?: string[];
    }) => (await http.post<Announcement>("/department/announcements", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useHideAnnouncement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) =>
      (await http.post<Announcement>(`/department/announcements/${id}/hide`, {})).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDeleteAnnouncement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await http.delete(`/department/announcements/${id}`);
    },
    onSuccess: () => invalidateAll(qc),
  });
}

export function useInventory(enabled = true) {
  return useQuery({
    queryKey: keys.inventory(),
    queryFn: async () => (await http.get<Page<InventoryItem>>("/department/inventory")).data,
    enabled,
  });
}

export function useInsertStock() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      department_id: number;
      sku: string;
      name: string;
      quantity: number;
    }) => (await http.post<InventoryItem>("/department/inventory", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useStockRequests() {
  return useQuery({
    queryKey: keys.stockRequests(),
    queryFn: async () => (await http.get<Page<StockRequest>>("/department/stock-requests")).data,
  });
}

export function useRequestStock() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { item_id: number; requested_quantity: number; purpose?: string }) =>
      (await http.post<StockRequest>("/department/stock-requests", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDecideStockRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (arg: { id: number; approve: boolean; note?: string }) =>
      (
        await http.post<StockRequest>(`/department/stock-requests/${arg.id}/decide`, {
          approve: arg.approve,
          note: arg.note ?? "",
        })
      ).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useIssueStock() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (arg: { id: number; note?: string }) =>
      (await http.post<StockRequest>(`/department/stock-requests/${arg.id}/issue`, {
        note: arg.note ?? "",
      })).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useStockMovements(enabled = true) {
  return useQuery({
    queryKey: keys.stockMovements(),
    queryFn: async () => (await http.get<Page<StockMovement>>("/department/stock-movements")).data,
    enabled,
  });
}

export function useFeedback() {
  return useQuery({
    queryKey: keys.feedback(),
    queryFn: async () => (await http.get<Page<Feedback>>("/department/feedback")).data,
  });
}

export function useSubmitFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { department_id: number; subject: string; body: string }) =>
      (await http.post<Feedback>("/department/feedback", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useReviewFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (arg: {
      id: number;
      category: string;
      close_as_simple?: boolean;
      note?: string;
    }) =>
      (
        await http.post<Feedback>(`/department/feedback/${arg.id}/review`, {
          category: arg.category,
          close_as_simple: Boolean(arg.close_as_simple),
          note: arg.note ?? "",
        })
      ).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDisposeFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (arg: { id: number; status: "resolved" | "closed"; note?: string }) =>
      (
        await http.post<Feedback>(`/department/feedback/${arg.id}/dispose`, {
          status: arg.status,
          note: arg.note ?? "",
        })
      ).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useTimetables() {
  return useQuery({
    queryKey: keys.timetables(),
    queryFn: async () => (await http.get<Page<TimetableSlot>>("/department/timetables")).data,
  });
}

export function useCreateTimetableSlot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      department_id: number;
      slot_kind: string;
      program: string;
      academic_year: string;
      section: string;
      course_code: string;
      course_title: string;
      room: string;
      day_of_week: number;
      start_time: string;
      end_time: string;
    }) => (await http.post<TimetableSlot>("/department/timetables", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useLabs() {
  return useQuery({
    queryKey: keys.labs(),
    queryFn: async () => (await http.get<Page<LabResource>>("/department/labs")).data,
  });
}

export function useCreateLab() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      department_id: number;
      lab_code: string;
      name: string;
      location?: string;
      capacity?: number;
      equipment_summary?: string;
    }) => (await http.post<LabResource>("/department/labs", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function usePrograms(enabled = true) {
  return useQuery({
    queryKey: keys.programs(),
    queryFn: async () => (await http.get<Page<DepartmentProgram>>("/department/programs")).data,
    enabled,
  });
}

export function useProfiles() {
  return useQuery({
    queryKey: keys.profiles(),
    queryFn: async () =>
      (await http.get<{ results: DepartmentProfile[] }>("/department/profiles")).data,
  });
}

export function useCreateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      department_id: number;
      user_id: number;
      profile_kind: string;
      display_name: string;
      program?: string;
    }) => (await http.post<DepartmentProfile>("/department/profiles", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}

export function useRoleAssignments() {
  return useQuery({
    queryKey: keys.roleAssignments(),
    queryFn: async () =>
      (await http.get<Page<RoleAssignment>>("/department/role-assignments")).data,
  });
}

export function useAssignRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      department_id: number;
      role_type: string;
      user_id: number;
      valid_from: string;
      valid_to: string;
    }) => (await http.post<RoleAssignment>("/department/role-assignments", body)).data,
    onSuccess: () => invalidateAll(qc),
  });
}
