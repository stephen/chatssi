import { useState } from "react";
import { useLocation } from "wouter";
import ChatTextbox from "./ChatTextbox";

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
      <ChatTextbox
        value={message}
        onChange={setMessage}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
