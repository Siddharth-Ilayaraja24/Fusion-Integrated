import { useState } from "react";
import {
  Badge, Button, Card, Container, Group, Stack, Text, Textarea, TextInput,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";

import { useAuth } from "../../../auth/AuthProvider";
import { errorMessage } from "../../../lib/http";
import { ErrorState } from "../../../ui/components/ErrorState";
import { FormModal } from "../../../ui/components/FormModal";
import { PageHeader } from "../../../ui/components/PageHeader";
import {
  useAnnouncements,
  useCreateAnnouncement,
  useDeleteAnnouncement,
  useDepartments,
  useHideAnnouncement,
} from "../api/hooks";

export default function AnnouncementsPage() {
  const { data, isPending, error } = useAnnouncements();
  const { data: depts } = useDepartments();
  const { can } = useAuth();
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [rolesText, setRolesText] = useState("student,faculty");

  const create = useCreateAnnouncement();
  const hide = useHideAnnouncement();
  const remove = useDeleteAnnouncement();

  const canCreate = can("department.announcement.create");
  const canUpdate = can("department.announcement.update");
  const canDelete = can("department.announcement.delete");

  if (error) return <Container size="md"><ErrorState error={error} /></Container>;

  const rows = data?.results ?? [];
  const defaultDeptId = depts?.results?.[0]?.id ?? 1;

  return (
    <Container size="md">
      <PageHeader
        title="Department Announcements"
        subtitle="Targeted department notices filtered by role, program, and academic year"
        action={
          canCreate && (
            <Button onClick={() => setCreating(true)}>New announcement</Button>
          )
        }
      />

      {isPending && <Text c="dimmed">Loading announcements…</Text>}

      {!isPending && rows.length === 0 && (
        <Card padding="xl" withBorder>
          <Text fw={600}>No announcements yet</Text>
          <Text size="sm" c="dimmed">Relevant active notices will appear here.</Text>
        </Card>
      )}

      <Stack gap="md">
        {rows.map((a) => (
          <Card key={a.id} padding="lg" withBorder>
            <Group justify="space-between" align="flex-start">
              <Stack gap={4} style={{ flex: 1 }}>
                <Group gap="xs">
                  <Text fw={700}>{a.title}</Text>
                  <Badge variant="light" size="sm">{a.status}</Badge>
                </Group>
                <Text size="sm">{a.content}</Text>
                <Text size="xs" c="dimmed">
                  Targets: {a.target_roles.join(", ")}
                </Text>
              </Stack>
              <Group gap="xs">
                {canUpdate && a.status === "active" && (
                  <Button
                    size="xs"
                    variant="subtle"
                    onClick={() =>
                      hide.mutate(a.id, {
                        onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
                      })
                    }
                  >
                    Hide
                  </Button>
                )}
                {canDelete && (
                  <Button
                    size="xs"
                    variant="subtle"
                    color="red"
                    onClick={() =>
                      remove.mutate(a.id, {
                        onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
                      })
                    }
                  >
                    Delete
                  </Button>
                )}
              </Group>
            </Group>
          </Card>
        ))}
      </Stack>

      <FormModal
        opened={creating}
        onClose={() => setCreating(false)}
        title="Create announcement"
        submitLabel="Publish"
        submitting={create.isPending}
        onSubmit={() => {
          create.mutate(
            {
              department_id: defaultDeptId,
              title,
              content,
              target_roles: rolesText.split(",").map((r) => r.trim()).filter(Boolean),
            },
            {
              onSuccess: () => {
                setTitle("");
                setContent("");
                setCreating(false);
                notifications.show({ color: "green", message: "Announcement published." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <TextInput label="Title" value={title} onChange={(e) => setTitle(e.currentTarget.value)} required />
          <Textarea label="Content" value={content} onChange={(e) => setContent(e.currentTarget.value)} required />
          <TextInput
            label="Target roles"
            value={rolesText}
            onChange={(e) => setRolesText(e.currentTarget.value)}
            required
          />
        </Stack>
      </FormModal>
    </Container>
  );
}
