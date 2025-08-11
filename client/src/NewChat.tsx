import { Button, Textarea } from "@mantine/core";
import { useState } from "react";
import { useLocation } from "wouter";

export default function NewChat() {
  const [message, setMessage] = useState("");
  const [, navigate] = useLocation();

  const handleSubmit = () => {
    if (!message.trim()) return;
    
    // Generate a new chat ID and redirect with the message as URL param
    const chatId = crypto.randomUUID();
    navigate(`/chats/${chatId}?message=${encodeURIComponent(message)}`);
  };

  return (
    <div>
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
        disabled={!message.trim()}
        mb="md"
        fullWidth
      >
        Start New Chat
      </Button>
    </div>
  );
}
