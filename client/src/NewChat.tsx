import { Button, Text, Textarea } from "@mantine/core";
import { useState } from "react";

export default function NewChat() {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState("");
  const [chatId, setChatId] = useState<string | null>(null);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!message.trim()) return;

    setIsLoading(true);

    // Generate or use existing chat ID
    const useChatId = currentChatId || crypto.randomUUID();
    if (!currentChatId) {
      setCurrentChatId(useChatId);
      setResponse(""); // Clear response for new chat
    }

    try {
      const apiResponse = await fetch(`/api/chats/${useChatId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
        credentials: "include",
      });

      if (!apiResponse.ok) throw new Error("Failed to send message");

      const reader = apiResponse.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let assistantResponse = "";
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");

          // Keep the last line in buffer (might be incomplete)
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim()) continue;

            try {
              const parsed = JSON.parse(line);
              if (parsed.type === "done") {
                console.log("Stream completed");
                // Add the complete response to conversation
                setResponse(
                  (prev) =>
                    prev +
                    `\n\nYou: ${message}\nAssistant: ${assistantResponse}\n`
                );
                break;
              } else if (parsed.type === "chat_created") {
                setChatId(parsed.chat_id);
              } else if (parsed.type === "content") {
                assistantResponse += parsed.content;
                // Update UI in real-time
                setResponse((prev) => {
                  const lines = prev.split("\n\n");
                  if (
                    lines.length > 0 &&
                    lines[lines.length - 1].startsWith("Assistant:")
                  ) {
                    // Update current assistant response
                    lines[lines.length - 1] = `Assistant: ${assistantResponse}`;
                  } else {
                    // Start new assistant response
                    lines.push(
                      `You: ${message}`,
                      `Assistant: ${assistantResponse}`
                    );
                  }
                  return lines.join("\n\n");
                });
              }
            } catch (e) {
              console.log("Failed to parse JSON:", line);
            }
          }
        }
      }

      setMessage("");
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        {currentChatId && (
          <Text size="sm" c="dimmed" style={{ alignSelf: "center" }}>
            Chat: {currentChatId.slice(0, 8)}...
          </Text>
        )}
      </div>

      <Textarea
        placeholder="Type your message here..."
        value={message}
        onChange={(e) => setMessage(e.currentTarget.value)}
        minRows={3}
        autosize
        mb="md"
      />
      <Button
        onClick={handleSubmit}
        loading={isLoading}
        disabled={!message.trim()}
        mb="md"
        fullWidth
      >
        {currentChatId ? "Send Message" : "Start New Chat"}
      </Button>

      {response && (
        <div
          style={{
            padding: "16px",
            backgroundColor: "#f8f9fa",
            borderRadius: "8px",
            whiteSpace: "pre-wrap",
            fontFamily: "monospace",
            fontSize: "14px",
            maxHeight: "400px",
            overflowY: "auto",
          }}
        >
          <Text size="sm" fw={500} mb="xs">
            Conversation:
          </Text>
          {response}
        </div>
      )}
    </div>
  );
}
