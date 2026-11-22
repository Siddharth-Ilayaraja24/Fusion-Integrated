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
  useDepartments,
  useDisposeFeedback,
  useFeedback,
  useReviewFeedback,
  useSubmitFeedback,
} from "../api/hooks";

export default function FeedbackPage() {
  const { data, isPending, error } = useFeedback();
  const { data: depts } = useDepartments();
  const { can } = useAuth();

  const [submitting, setSubmitting] = useState(false);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const submit = useSubmitFeedback();
  const review = useReviewFeedback();
  const dispose = useDisposeFeedback();

  const canSubmit = can("department.feedback.create");
  const canReview = can("department.feedback.review");
  const canDispose = can("department.feedback.update");

  if (error) return <Container size="md"><ErrorState error={error} /></Container>;

  const rows = data?.results ?? [];
  const defaultDeptId = depts?.results?.[0]?.id ?? 1;

  return (
    <Container size="md">
      <PageHeader
        title="Confidential Feedback"
        subtitle="Submit department feedback and track initial review and resolution"
        action={
          canSubmit && (
            <Button onClick={() => setSubmitting(true)}>Submit feedback</Button>
          )
        }
      />

      {isPending && <Text c="dimmed">Loading feedback…</Text>}

      {!isPending && rows.length === 0 && (
        <Card padding="xl" withBorder>
          <Text fw={600}>No feedback items</Text>
          <Text size="sm" c="dimmed">Your confidential feedback items will appear here.</Text>
        </Card>
      )}

      <Stack gap="md">
        {rows.map((fb) => (
          <Card key={fb.id} padding="lg" withBorder>
            <Group justify="space-between" align="flex-start">
              <Stack gap={4} style={{ flex: 1 }}>
                <Group gap="xs">
                  <Text fw={700}>{fb.subject}</Text>
                  <Badge variant="light">{fb.status}</Badge>
                  {fb.category && <Badge color="gray" variant="outline">{fb.category}</Badge>}
                </Group>
                <Text size="sm">{fb.body}</Text>
              </Stack>
              <Group gap="xs">
                {canReview && fb.status === "new" && (
                  <Button
                    size="xs"
                    variant="light"
                    onClick={() => review.mutate({ id: fb.id, category: "General" })}
                  >
                    Mark reviewed
                  </Button>
                )}
                {canDispose && fb.status === "under_review" && (
                  <Button
                    size="xs"
                    color="green"
                    onClick={() => dispose.mutate({ id: fb.id, status: "resolved" })}
                  >
                    Resolve
                  </Button>
                )}
              </Group>
            </Group>
          </Card>
        ))}
      </Stack>

      <FormModal
        opened={submitting}
        onClose={() => setSubmitting(false)}
        title="Submit confidential feedback"
        submitLabel="Submit"
        submitting={submit.isPending}
        onSubmit={() => {
          submit.mutate(
            { department_id: defaultDeptId, subject, body },
            {
              onSuccess: () => {
                setSubject("");
                setBody("");
                setSubmitting(false);
                notifications.show({ color: "green", message: "Feedback submitted." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <TextInput label="Subject" value={subject} onChange={(e) => setSubject(e.currentTarget.value)} required />
          <Textarea label="Message" value={body} onChange={(e) => setBody(e.currentTarget.value)} required />
        </Stack>
      </FormModal>
    </Container>
  );
}
