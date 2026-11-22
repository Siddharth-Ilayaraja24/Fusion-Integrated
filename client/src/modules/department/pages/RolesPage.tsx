import { useState } from "react";
import {
  Badge, Button, Card, Container, Group, NumberInput, Select, Stack, Text, TextInput,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";

import { useAuth } from "../../../auth/AuthProvider";
import { errorMessage } from "../../../lib/http";
import { ErrorState } from "../../../ui/components/ErrorState";
import { FormModal } from "../../../ui/components/FormModal";
import { PageHeader } from "../../../ui/components/PageHeader";
import { useAssignRole, useDepartments, useRoleAssignments } from "../api/hooks";

export default function RolesPage() {
  const { data, isPending, error } = useRoleAssignments();
  const { data: depts } = useDepartments();
  const { can } = useAuth();

  const [assigning, setAssigning] = useState(false);
  const [roleType, setRoleType] = useState("hod");
  const [userId, setUserId] = useState<number>(3001);
  const [validFrom, setValidFrom] = useState("2026-08-01T00:00:00Z");
  const [validTo, setValidTo] = useState("2028-07-31T23:59:59Z");

  const assign = useAssignRole();
  const canAssign = can("department.role_assignment.assign");

  if (error) return <Container size="md"><ErrorState error={error} /></Container>;

  const rows = data?.results ?? [];
  const defaultDeptId = depts?.results?.[0]?.id ?? 1;

  return (
    <Container size="md">
      <PageHeader
        title="Department Role Assignments"
        subtitle="Time-bound HOD and Dept_Admin assignments managed by central administration"
        action={canAssign && <Button onClick={() => setAssigning(true)}>Assign role</Button>}
      />

      {isPending && <Text c="dimmed">Loading role assignments…</Text>}

      {!isPending && rows.length === 0 && (
        <Card padding="xl" withBorder>
          <Text fw={600}>No role assignments recorded</Text>
          <Text size="sm" c="dimmed">Scheduled and active HOD/Dept_Admin tenures appear here.</Text>
        </Card>
      )}

      <Stack gap="md">
        {rows.map((r) => (
          <Card key={r.id} padding="md" withBorder>
            <Group justify="space-between">
              <Stack gap={2}>
                <Group gap="xs">
                  <Text fw={700}>{r.role_type.toUpperCase()} — User #{r.user_id}</Text>
                  <Badge variant="light">{r.status}</Badge>
                </Group>
                <Text size="xs" c="dimmed">
                  {r.valid_from} → {r.valid_to}
                </Text>
              </Stack>
              <Badge variant="outline">Dept #{r.department_id}</Badge>
            </Group>
          </Card>
        ))}
      </Stack>

      <FormModal
        opened={assigning}
        onClose={() => setAssigning(false)}
        title="Assign department role"
        submitLabel="Save assignment"
        submitting={assign.isPending}
        onSubmit={() => {
          assign.mutate(
            {
              department_id: defaultDeptId,
              role_type: roleType,
              user_id: userId,
              valid_from: validFrom,
              valid_to: validTo,
            },
            {
              onSuccess: () => {
                setAssigning(false);
                notifications.show({ color: "green", message: "Role assignment saved." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <Select
            label="Role type"
            value={roleType}
            onChange={(v) => setRoleType(v ?? "hod")}
            data={[
              { value: "hod", label: "HOD" },
              { value: "dept_admin", label: "Dept_Admin" },
            ]}
          />
          <NumberInput label="Employee user ID" min={1} value={userId} onChange={(v) => setUserId(Number(v) || 1)} />
          <TextInput label="Valid from (ISO)" value={validFrom} onChange={(e) => setValidFrom(e.currentTarget.value)} required />
          <TextInput label="Valid to (ISO)" value={validTo} onChange={(e) => setValidTo(e.currentTarget.value)} required />
        </Stack>
      </FormModal>
    </Container>
  );
}
