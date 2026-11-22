import { lazy, type ReactElement } from "react";
import { Navigate, type RouteObject } from "react-router-dom";

import { RequireDeptPermission } from "./components/RequireDeptPermission";

const AnnouncementsPage = lazy(() => import("./pages/AnnouncementsPage"));
const InventoryPage = lazy(() => import("./pages/InventoryPage"));
const FeedbackPage = lazy(() => import("./pages/FeedbackPage"));
const TimetablePage = lazy(() => import("./pages/TimetablePage"));
const ResourcesPage = lazy(() => import("./pages/ResourcesPage"));
const ProfilesPage = lazy(() => import("./pages/ProfilesPage"));
const DetailsPage = lazy(() => import("./pages/DetailsPage"));
const RolesPage = lazy(() => import("./pages/RolesPage"));

function guarded(permission: string, page: ReactElement) {
  return <RequireDeptPermission permission={permission}>{page}</RequireDeptPermission>;
}

export const routes: RouteObject[] = [
  { index: true, element: <Navigate to="details" replace /> },
  { path: "announcements", element: guarded("department.announcement.view", <AnnouncementsPage />) },
  { path: "inventory", element: guarded("department.stock_request.view", <InventoryPage />) },
  { path: "feedback", element: guarded("department.feedback.view", <FeedbackPage />) },
  { path: "timetable", element: guarded("department.timetable.view", <TimetablePage />) },
  { path: "resources", element: guarded("department.lab.view", <ResourcesPage />) },
  { path: "profiles", element: guarded("department.profile.view", <ProfilesPage />) },
  { path: "details", element: guarded("department.department.view", <DetailsPage />) },
  { path: "roles", element: guarded("department.role_assignment.view", <RolesPage />) },
];
