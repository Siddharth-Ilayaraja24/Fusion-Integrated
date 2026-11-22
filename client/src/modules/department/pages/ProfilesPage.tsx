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
import { useCreateProfile, useDepartments, useProfiles } from "../api/hooks";

export default function ProfilesPage() {
  const { data, isPending, error } = useProfiles();
  const { data: depts } = useDepartments();
  const { can } = useAuth();

  const [adding, setAdding] = useState(false);
  const [userId, setUserId] = useState<number>(1001);
  const [kind, setKind] = useState<string>("student");
  const [displayName, setDisplayName] = useState("");
  const [program, setProgram] = useState("BTech");

  const createProfile = useCreateProfile();
  const canUpdate = can("department.profile.update");

  if (error) return <Container size="md"><ErrorState error={error} /></Container>;

  const rows = data?.results ?? [];
  const defaultDeptId = depts?.results?.[0]?.id ?? 1;

  return (
    <Container size="md">
      <PageHeader
        title="Department Profiles"
        subtitle="Role-scoped Faculty, Student, and Alumni directory"
        action={canUpdate && <Button onClick={() => setAdding(true)}>Add profile</Button>}
      />

      {isPending && <Text c="dimmed">Loading profiles…</Text>}

      {!isPending && rows.length === 0 && (
        <Card padding="xl" withBorder>
          <Text fw={600}>No visible profiles</Text>
          <Text size="sm" c="dimmed">Profiles permitted for your role will appear here.</Text>
        </Card>
      )}

      <Stack gap="md">
        {rows.map((p) => (
          <Card key={p.id} padding="md" withBorder>
            <Group justify="space-between">
              <Stack gap={2}>
                <Group gap="xs">
                  <Text fw={700}>{p.display_name}</Text>
                  <Badge variant="light">{p.profile_kind}</Badge>
                </Group>
                <Text size="sm" c="dimmed">
                  {p.program || p.designation_title || "Department member"}
                  {p.email ? ` · ${p.email}` : ""}
                </Text>
              </Stack>
              <Badge variant="outline" size="sm">{p.visibility_tier}</Badge>
            </Group>
          </Card>
        ))}
      </Stack>

      <FormModal
        opened={adding}
        onClose={() => setAdding(false)}
        title="Add department profile"
        submitLabel="Save profile"
        submitting={createProfile.isPending}
        onSubmit={() => {
          createProfile.mutate(
            {
              department_id: defaultDeptId,
              user_id: userId,
              profile_kind: kind,
              display_name: displayName,
              program,
            },
            {
              onSuccess: () => {
                setDisplayName("");
                setAdding(false);
                notifications.show({ color: "green", message: "Profile saved." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <NumberInput label="User ID" min={1} value={userId} onChange={(v) => setUserId(Number(v) || 1)} />
          <Select
            label="Profile kind"
            value={kind}
            onChange={(v) => setKind(v ?? "student")}
            data={[
              { value: "student", label: "Student" },
              { value: "faculty", label: "Faculty" },
              { value: "alumni", label: "Alumni" },
            ]}
          />
          <TextInput label="Display name" value={displayName} onChange={(e) => setDisplayName(e.currentTarget.value)} required />
          <TextInput label="Program" value={program} onChange={(e) => setProgram(e.currentTarget.value)} />
        </Stack>
      </FormModal>
    </Container>
  );
}
