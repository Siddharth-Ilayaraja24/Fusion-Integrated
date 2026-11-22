import { useState } from "react";
import {
  Badge, Button, Card, Container, Group, NumberInput, Stack, Text, TextInput,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";

import { useAuth } from "../../../auth/AuthProvider";
import { errorMessage } from "../../../lib/http";
import { ErrorState } from "../../../ui/components/ErrorState";
import { FormModal } from "../../../ui/components/FormModal";
import { PageHeader } from "../../../ui/components/PageHeader";
import {
  useCreateTimetableSlot,
  useDepartments,
  usePrograms,
  useTimetables,
} from "../api/hooks";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function TimetablePage() {
  const { data, isPending, error } = useTimetables();
  const { data: programs } = usePrograms();
  const { data: depts } = useDepartments();
  const { can } = useAuth();

  const [adding, setAdding] = useState(false);
  const [courseCode, setCourseCode] = useState("");
  const [courseTitle, setCourseTitle] = useState("");
  const [room, setRoom] = useState("");
  const [program, setProgram] = useState("BTech");
  const [day, setDay] = useState<number>(0);

  const createSlot = useCreateTimetableSlot();
  const canCreate = can("department.timetable.create");

  if (error) return <Container size="md"><ErrorState error={error} /></Container>;

  const rows = data?.results ?? [];
  const progRows = programs?.results ?? [];
  const defaultDeptId = depts?.results?.[0]?.id ?? 1;

  return (
    <Container size="md">
      <PageHeader
        title="Timetable & Academic Programs"
        subtitle="Conflict-free class/lab schedules and department academic programs"
        action={canCreate && <Button onClick={() => setAdding(true)}>Add slot</Button>}
      />

      {isPending && <Text c="dimmed">Loading timetable…</Text>}

      {!isPending && rows.length === 0 && (
        <Card padding="xl" withBorder>
          <Text fw={600}>No timetable slots published</Text>
          <Text size="sm" c="dimmed">Scheduled classes and labs will appear here.</Text>
        </Card>
      )}

      <Stack gap="md">
        {rows.map((slot) => (
          <Card key={slot.id} padding="md" withBorder>
            <Group justify="space-between">
              <Stack gap={2}>
                <Group gap="xs">
                  <Text fw={700}>{slot.course_code} — {slot.course_title}</Text>
                  <Badge variant="light">{slot.slot_kind}</Badge>
                </Group>
                <Text size="sm" c="dimmed">
                  {DAYS[slot.day_of_week] ?? slot.day_of_week} · {slot.start_time}–{slot.end_time} · Room {slot.room}
                </Text>
              </Stack>
              <Badge variant="outline">{slot.program} ({slot.section})</Badge>
            </Group>
          </Card>
        ))}

        {progRows.length > 0 && (
          <Card padding="md" withBorder>
            <Text fw={700} mb="xs">Academic Programs</Text>
            <Stack gap="xs">
              {progRows.map((p) => (
                <Text key={p.id} size="sm">
                  {p.code}: {p.name} ({p.degree_level}, {p.duration_years} yrs)
                </Text>
              ))}
            </Stack>
          </Card>
        )}
      </Stack>

      <FormModal
        opened={adding}
        onClose={() => setAdding(false)}
        title="Add timetable slot"
        submitLabel="Save slot"
        submitting={createSlot.isPending}
        onSubmit={() => {
          createSlot.mutate(
            {
              department_id: defaultDeptId,
              slot_kind: "class",
              program,
              academic_year: "2026-27",
              section: "A",
              course_code: courseCode,
              course_title: courseTitle,
              room,
              day_of_week: day,
              start_time: "09:00:00",
              end_time: "10:00:00",
            },
            {
              onSuccess: () => {
                setCourseCode("");
                setCourseTitle("");
                setRoom("");
                setAdding(false);
                notifications.show({ color: "green", message: "Timetable slot saved." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <TextInput label="Course code" value={courseCode} onChange={(e) => setCourseCode(e.currentTarget.value)} required />
          <TextInput label="Course title" value={courseTitle} onChange={(e) => setCourseTitle(e.currentTarget.value)} required />
          <TextInput label="Room" value={room} onChange={(e) => setRoom(e.currentTarget.value)} required />
          <TextInput label="Program" value={program} onChange={(e) => setProgram(e.currentTarget.value)} required />
          <NumberInput label="Day (0=Mon..6=Sun)" min={0} max={6} value={day} onChange={(v) => setDay(Number(v) || 0)} />
        </Stack>
      </FormModal>
    </Container>
  );
}
