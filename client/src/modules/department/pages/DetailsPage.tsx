import { useState } from "react";
import {
  Badge, Button, Card, Container, Group, Select, Stack, Text, Textarea,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";

import { useAuth } from "../../../auth/AuthProvider";
import { errorMessage } from "../../../lib/http";
import { ErrorState } from "../../../ui/components/ErrorState";
import { FormModal } from "../../../ui/components/FormModal";
import { PageHeader } from "../../../ui/components/PageHeader";
import {
  useDecideOfficialChange,
  useDepartments,
  useOfficialChanges,
  useProposeOfficialChange,
} from "../api/hooks";

export default function DetailsPage() {
  const { data, isPending, error } = useDepartments();
  const { can } = useAuth();
  const canViewChanges = can("department.official_change.view");
  const canUpdate = can("department.department.update");
  const canApprove = can("department.official_change.approve");

  const { data: changes } = useOfficialChanges(canViewChanges);
  const propose = useProposeOfficialChange();
  const decide = useDecideOfficialChange();

  const [proposing, setProposing] = useState(false);
  const [fieldName, setFieldName] = useState("core_policies");
  const [proposedValue, setProposedValue] = useState("");

  if (error) return <Container size="md"><ErrorState error={error} /></Container>;

  const rows = data?.results ?? [];
  const changeRows = changes?.results ?? [];
  const defaultDeptId = rows[0]?.id ?? 1;

  return (
    <Container size="md">
      <PageHeader
        title="Department Details"
        subtitle="Department overview, derived Headship, and HOD-approved official changes"
        action={
          canUpdate && (
            <Button onClick={() => setProposing(true)}>Propose official change</Button>
          )
        }
      />

      {isPending && <Text c="dimmed">Loading department details…</Text>}

      {!isPending && rows.length === 0 && (
        <Card padding="xl" withBorder>
          <Text fw={600}>No departments found</Text>
          <Text size="sm" c="dimmed">Seed departments to populate this view.</Text>
        </Card>
      )}

      <Stack gap="md">
        {rows.map((d) => (
          <Card key={d.id} padding="lg" withBorder>
            <Stack gap={4}>
              <Group gap="xs">
                <Text fw={700}>{d.code} — {d.name}</Text>
                <Badge variant="light">
                  HOD: {d.active_hod_user_id ? `User #${d.active_hod_user_id}` : "Unassigned"}
                </Badge>
              </Group>
              {d.description && <Text size="sm">{d.description}</Text>}
              {d.core_policies && (
                <Text size="xs" c="dimmed">Core policies: {d.core_policies}</Text>
              )}
            </Stack>
          </Card>
        ))}

        {changeRows.length > 0 && (
          <Card padding="lg" withBorder>
            <Text fw={700} mb="sm">Official Detail Change Requests</Text>
            <Stack gap="sm">
              {changeRows.map((c) => (
                <Group key={c.id} justify="space-between">
                  <Stack gap={2}>
                    <Group gap="xs">
                      <Text size="sm" fw={600}>{c.field_name}</Text>
                      <Badge variant="light">{c.status}</Badge>
                    </Group>
                    <Text size="xs" c="dimmed">Proposed: {c.proposed_value}</Text>
                  </Stack>
                  {canApprove && c.status === "pending_hod_approval" && (
                    <Group gap="xs">
                      <Button
                        size="xs"
                        color="green"
                        onClick={() => decide.mutate({ id: c.id, approve: true })}
                      >
                        Approve
                      </Button>
                      <Button
                        size="xs"
                        color="red"
                        variant="subtle"
                        onClick={() => decide.mutate({ id: c.id, approve: false })}
                      >
                        Reject
                      </Button>
                    </Group>
                  )}
                </Group>
              ))}
            </Stack>
          </Card>
        )}
      </Stack>

      <FormModal
        opened={proposing}
        onClose={() => setProposing(false)}
        title="Propose official department change"
        submitLabel="Submit for HOD approval"
        submitting={propose.isPending}
        onSubmit={() => {
          propose.mutate(
            { department_id: defaultDeptId, field_name: fieldName, proposed_value: proposedValue },
            {
              onSuccess: () => {
                setProposedValue("");
                setProposing(false);
                notifications.show({ color: "green", message: "Official change submitted." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <Select
            label="Official field"
            value={fieldName}
            onChange={(v) => setFieldName(v ?? "core_policies")}
            data={[
              { value: "name", label: "Department Name" },
              { value: "core_policies", label: "Core Policies" },
            ]}
          />
          <Textarea
            label="Proposed value"
            value={proposedValue}
            onChange={(e) => setProposedValue(e.currentTarget.value)}
            required
          />
        </Stack>
      </FormModal>
    </Container>
  );
}
