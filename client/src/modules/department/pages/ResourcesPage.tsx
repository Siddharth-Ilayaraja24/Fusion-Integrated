import { useState } from "react";
import {
  Badge, Button, Card, Container, Group, NumberInput, Stack, Text, Textarea, TextInput,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";

import { useAuth } from "../../../auth/AuthProvider";
import { errorMessage } from "../../../lib/http";
import { ErrorState } from "../../../ui/components/ErrorState";
import { FormModal } from "../../../ui/components/FormModal";
import { PageHeader } from "../../../ui/components/PageHeader";
import { useCreateLab, useDepartments, useLabs } from "../api/hooks";

export default function ResourcesPage() {
  const { data, isPending, error } = useLabs();
  const { data: depts } = useDepartments();
  const { can } = useAuth();

  const [adding, setAdding] = useState(false);
  const [labCode, setLabCode] = useState("");
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [capacity, setCapacity] = useState<number>(30);
  const [equipment, setEquipment] = useState("");

  const createLab = useCreateLab();
  const canUpdate = can("department.lab.update");

  if (error) return <Container size="md"><ErrorState error={error} /></Container>;

  const rows = data?.results ?? [];
  const defaultDeptId = depts?.results?.[0]?.id ?? 1;

  return (
    <Container size="md">
      <PageHeader
        title="Lab Resources"
        subtitle="Department laboratory equipment and capacity profiles"
        action={canUpdate && <Button onClick={() => setAdding(true)}>Add lab</Button>}
      />

      {isPending && <Text c="dimmed">Loading lab resources…</Text>}

      {!isPending && rows.length === 0 && (
        <Card padding="xl" withBorder>
          <Text fw={600}>No lab resources recorded</Text>
          <Text size="sm" c="dimmed">Department lab equipment profiles will appear here.</Text>
        </Card>
      )}

      <Stack gap="md">
        {rows.map((lab) => (
          <Card key={lab.id} padding="lg" withBorder>
            <Group justify="space-between">
              <Stack gap={4}>
                <Group gap="xs">
                  <Text fw={700}>{lab.lab_code} — {lab.name}</Text>
                  <Badge variant="light">{lab.status}</Badge>
                </Group>
                <Text size="sm" c="dimmed">
                  {lab.location || "Location unset"} · Capacity {lab.capacity}
                </Text>
                {lab.equipment_summary && <Text size="sm">{lab.equipment_summary}</Text>}
              </Stack>
            </Group>
          </Card>
        ))}
      </Stack>

      <FormModal
        opened={adding}
        onClose={() => setAdding(false)}
        title="Add lab resource"
        submitLabel="Save lab"
        submitting={createLab.isPending}
        onSubmit={() => {
          createLab.mutate(
            {
              department_id: defaultDeptId,
              lab_code: labCode,
              name,
              location,
              capacity,
              equipment_summary: equipment,
            },
            {
              onSuccess: () => {
                setLabCode("");
                setName("");
                setLocation("");
                setEquipment("");
                setAdding(false);
                notifications.show({ color: "green", message: "Lab resource saved." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <TextInput label="Lab code" value={labCode} onChange={(e) => setLabCode(e.currentTarget.value)} required />
          <TextInput label="Lab name" value={name} onChange={(e) => setName(e.currentTarget.value)} required />
          <TextInput label="Location" value={location} onChange={(e) => setLocation(e.currentTarget.value)} />
          <NumberInput label="Capacity" min={0} value={capacity} onChange={(v) => setCapacity(Number(v) || 0)} />
          <Textarea label="Equipment summary" value={equipment} onChange={(e) => setEquipment(e.currentTarget.value)} />
        </Stack>
      </FormModal>
    </Container>
  );
}
