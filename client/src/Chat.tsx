import { Text } from "@mantine/core";
import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useRoute } from "wouter";
import { chatById } from "./api-client";
import ChatTextbox from "./ChatTextbox";

export default function Chat() {
  const [match, params] = useRoute("/chats/:id");
  const [, , router] = useLocation();
  const chatId = params?.id;

  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<
    Array<{ id: string; type: "user" | "assistant"; content: string }>
  >([]);
  const initialMessageProcessed = useRef(false);
  const [isLoadingChat, setIsLoadingChat] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
                  break;
                } else if (parsed.type === "chat_created") {
                  console.log("Chat created:", parsed.chat_id);
                } else if (parsed.type === "content") {
                  assistantResponse += parsed.content;
                  // Update UI in real-time
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];

                    if (lastMessage && lastMessage.type === "assistant") {
                      // Update current assistant response with accumulated content
                      lastMessage.content = assistantResponse;
                    } else {
                      // Start new conversation - add user message and assistant response
                      if (
                        !newMessages.some(
                          (m) =>
                            m.content === messageToSend && m.type === "user"
                        )
                      ) {
                        newMessages.push({
                          id: `user-${Date.now()}`,
                          type: "user",
                          content: messageToSend,
                        });
                      }
                      newMessages.push({
                        id: `assistant-${Date.now()}`,
                        type: "assistant",
                        content: assistantResponse,
                      });
                    }
                    return newMessages;
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
    if (initialMessageProcessed.current) return;

    const urlParams = new URLSearchParams(window.location.search);
    const initialMessage = urlParams.get("message");
    if (initialMessage) {
      initialMessageProcessed.current = true;
      setMessage(initialMessage);
      setTimeout(() => {
        handleSubmitWithMessage(initialMessage);
      }, 0);
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [handleSubmitWithMessage]);

  // Fetch existing chat messages when component mounts
  useEffect(() => {
    if (!chatId) return;

    // Check if this is a new chat with an initial message
    const urlParams = new URLSearchParams(window.location.search);
    const initialMessage = urlParams.get("message");

    // Skip fetching if this is a new chat with an initial message
    if (initialMessage) {
      setIsLoadingChat(false);
      return;
    }

    const fetchChatMessages = async () => {
      try {
        setIsLoadingChat(true);
        const result = await chatById({
          path: { chat_id: chatId },
        });

        if (result.data && result.data.messages) {
          // Convert API messages to array format
          const messageArray = result.data.messages.map(
            (msg: any, index: number) => ({
              id: `${msg.message_type}-${index}`,
              type:
                msg.message_type === "user"
                  ? ("user" as const)
                  : ("assistant" as const),
              content: msg.content,
            })
          );
          setMessages(messageArray);
        }
      } catch (error) {
        console.error("Failed to fetch chat messages:", error);
      } finally {
        setIsLoadingChat(false);
      }
    };

    fetchChatMessages();
  }, [chatId]);

  const handleSubmit = async () => {
    await handleSubmitWithMessage(message);
  };

  if (!match) {
    return <div>Chat not found</div>;
  }

  return (
    <div
      style={{
        width: "100%",
        height: "90vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          paddingBottom: "8px",
        }}
      >
        {isLoadingChat &&
          messages.map((message) => {
            const isUser = message.type === "user";

            return (
              <section
                key={message.id}
                style={{
                  display: "flex",
                  padding: "16px",
                  backgroundColor: isUser ? "#e3f2fd" : "#f8f9fa",
                  borderRadius: "8px",
                  marginBottom: "8px",
                  whiteSpace: "pre-wrap",
                  fontFamily: "monospace",
                  fontSize: "14px",
                  gap: "16px",
                }}
              >
                <Text
                  size="sm"
                  fw={500}
                  c={isUser ? "blue" : "gray"}
                  style={{ minWidth: "80px", flexShrink: 0 }}
                >
                  {isUser ? "You" : "Assistant"}:
                </Text>
                <div style={{ flex: 1 }}>{message.content}</div>
              </section>
            );
          })}
        <div ref={messagesEndRef} />
      </div>

      <div
        style={{
          padding: "16px",
          borderTop: "1px solid #eee",
          backgroundColor: "white",
        }}
      >
        <ChatTextbox
          value={message}
          onChange={setMessage}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
