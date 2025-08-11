import { Button, Card, Group, Textarea } from "@mantine/core";

interface ChatTextboxProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading?: boolean;
  placeholder?: string;
}

export default function ChatTextbox({
  value,
  onChange,
  onSubmit,
  isLoading = false,
  placeholder = "Type your message here...",
}: ChatTextboxProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Card.Section>
        <Group align="flex-end" gap="md" mb="md">
          <Textarea
            placeholder={placeholder}
            value={value}
            onChange={(e) => onChange(e.currentTarget.value)}
            onKeyDown={handleKeyDown}
            minRows={3}
            autosize
            style={{ flex: 1 }}
          />
          <Button
            onClick={onSubmit}
            loading={isLoading}
            disabled={!value.trim() || isLoading}
          >
            ⬆️
          </Button>
        </Group>
      </Card.Section>
    </Card>
  );
}
