import { Container, Text, Title } from "@mantine/core";
import type { ReactNode } from "react";

import { useAuth } from "../../../auth/AuthProvider";

interface Props {
  permission: string;
  children: ReactNode;
}

export function RequireDeptPermission({ permission, children }: Props) {
  const { can } = useAuth();
  if (!can(permission)) {
    return (
      <Container size="md" mt="xl">
        <Title order={3}>Not permitted</Title>
        <Text c="dimmed" mt="xs">
          Your active role does not have permission to view this department screen.
        </Text>
      </Container>
    );
  }
  return <>{children}</>;
}
