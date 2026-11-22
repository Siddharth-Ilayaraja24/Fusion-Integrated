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
  useDecideStockRequest,
  useDepartments,
  useInsertStock,
  useInventory,
  useIssueStock,
  useRequestStock,
  useStockRequests,
} from "../api/hooks";

export default function InventoryPage() {
  const { data: reqs, isPending, error } = useStockRequests();
  const { data: inv } = useInventory();
  const { data: depts } = useDepartments();
  const { can } = useAuth();

  const [addingStock, setAddingStock] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [qty, setQty] = useState<number>(1);
  const [itemId, setItemId] = useState<number>(1);
  const [reqQty, setReqQty] = useState<number>(1);
  const [purpose, setPurpose] = useState("");

  const insertStock = useInsertStock();
  const requestStock = useRequestStock();
  const decide = useDecideStockRequest();
  const issue = useIssueStock();

  const canInsert = can("department.inventory.create");
  const canRequest = can("department.stock_request.create");
  const canApprove = can("department.stock_request.approve");
  const canIssue = can("department.stock_request.update");

  if (error) return <Container size="md"><ErrorState error={error} /></Container>;

  const rows = reqs?.results ?? [];
  const items = inv?.results ?? [];
  const defaultDeptId = depts?.results?.[0]?.id ?? 1;

  return (
    <Container size="md">
      <PageHeader
        title="Inventory & Stock Requests"
        subtitle="Department stock catalog, Faculty requests, HOD approval, and issuance"
        action={
          <Group gap="xs">
            {canInsert && (
              <Button variant="light" onClick={() => setAddingStock(true)}>Insert stock</Button>
            )}
            {canRequest && (
              <Button onClick={() => {
                if (items[0]) setItemId(items[0].id);
                setRequesting(true);
              }}>
                Request stock
              </Button>
            )}
          </Group>
        }
      />

      {isPending && <Text c="dimmed">Loading stock requests…</Text>}

      {!isPending && rows.length === 0 && (
        <Card padding="xl" withBorder>
          <Text fw={600}>No stock requests yet</Text>
          <Text size="sm" c="dimmed">Inventory requests and approvals will appear here.</Text>
        </Card>
      )}

      <Stack gap="md">
        {rows.map((r) => (
          <Card key={r.id} padding="lg" withBorder>
            <Group justify="space-between" align="center">
              <Stack gap={2}>
                <Group gap="xs">
                  <Text fw={700}>{r.item_name} ({r.item_sku})</Text>
                  <Badge variant="light">{r.status}</Badge>
                </Group>
                <Text size="sm">Quantity: {r.requested_quantity} {r.purpose ? `· ${r.purpose}` : ""}</Text>
              </Stack>
              <Group gap="xs">
                {canApprove && r.status === "pending_hod_approval" && (
                  <>
                    <Button
                      size="xs"
                      color="green"
                      onClick={() => decide.mutate({ id: r.id, approve: true })}
                    >
                      Approve
                    </Button>
                    <Button
                      size="xs"
                      color="red"
                      variant="subtle"
                      onClick={() => decide.mutate({ id: r.id, approve: false })}
                    >
                      Reject
                    </Button>
                  </>
                )}
                {canIssue && r.status === "approved_for_issuance" && (
                  <Button size="xs" onClick={() => issue.mutate({ id: r.id })}>
                    Issue stock
                  </Button>
                )}
              </Group>
            </Group>
          </Card>
        ))}
      </Stack>

      <FormModal
        opened={addingStock}
        onClose={() => setAddingStock(false)}
        title="Insert inventory stock"
        submitLabel="Save stock"
        submitting={insertStock.isPending}
        onSubmit={() => {
          insertStock.mutate(
            { department_id: defaultDeptId, sku, name, quantity: qty },
            {
              onSuccess: () => {
                setSku("");
                setName("");
                setAddingStock(false);
                notifications.show({ color: "green", message: "Stock inserted." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <TextInput label="SKU" value={sku} onChange={(e) => setSku(e.currentTarget.value)} required />
          <TextInput label="Item name" value={name} onChange={(e) => setName(e.currentTarget.value)} required />
          <NumberInput label="Quantity" min={1} value={qty} onChange={(v) => setQty(Number(v) || 1)} />
        </Stack>
      </FormModal>

      <FormModal
        opened={requesting}
        onClose={() => setRequesting(false)}
        title="Request stock item"
        submitLabel="Submit request"
        submitting={requestStock.isPending}
        onSubmit={() => {
          requestStock.mutate(
            { item_id: itemId, requested_quantity: reqQty, purpose },
            {
              onSuccess: () => {
                setPurpose("");
                setRequesting(false);
                notifications.show({ color: "green", message: "Stock request submitted." });
              },
              onError: (e) => notifications.show({ color: "red", message: errorMessage(e) }),
            },
          );
        }}
      >
        <Stack gap="sm">
          <NumberInput label="Item ID" min={1} value={itemId} onChange={(v) => setItemId(Number(v) || 1)} />
          <NumberInput
            label="Requested quantity"
            min={1}
            value={reqQty}
            onChange={(v) => setReqQty(Number(v) || 1)}
          />
          <TextInput label="Purpose" value={purpose} onChange={(e) => setPurpose(e.currentTarget.value)} />
        </Stack>
      </FormModal>
    </Container>
  );
}
