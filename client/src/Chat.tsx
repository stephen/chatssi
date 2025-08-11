import { Button, Text, Textarea } from "@mantine/core";
import { useCallback, useEffect, useState } from "react";
import { useLocation, useRoute } from "wouter";

export default function Chat() {
  const [match, params] = useRoute("/chats/:id");
  const [, , router] = useLocation();
  const chatId = params?.id;

  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState("");

  const handleSubmitWithMessage = useCallback(
    async (messageToSend: string) => {
      if (!messageToSend.trim() || !chatId) return;

      setIsLoading(true);

      try {
        const apiResponse = await fetch(`/api/chats/${chatId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: messageToSend }),
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
                      `\n\nYou: ${messageToSend}\nAssistant: ${assistantResponse}\n`
                  );
                  break;
                } else if (parsed.type === "chat_created") {
                  console.log("Chat created:", parsed.chat_id);
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
                      lines[
                        lines.length - 1
                      ] = `Assistant: ${assistantResponse}`;
                    } else {
                      // Start new assistant response
                      lines.push(
                        `You: ${messageToSend}`,
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
    },
    [chatId]
  );

  // Handle initial message from URL params
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const initialMessage = urlParams.get('message');
    if (initialMessage) {
      setMessage(initialMessage);
      // Auto-submit the initial message
      setTimeout(() => {
        handleSubmitWithMessage(initialMessage);
      }, 0);
      // Clean up the URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [handleSubmitWithMessage]);

  const handleSubmit = async () => {
    await handleSubmitWithMessage(message);
  };

  if (!match) {
    return <div>Chat not found</div>;
  }

  return (
    <div>
      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        <Text size="sm" c="dimmed" style={{ alignSelf: "center" }}>
          Chat: {chatId?.slice(0, 8)}...
        </Text>
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
        Send Message
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
