import { AppShell, AppShellMain } from "@mantine/core";
import "./App.css";

function App() {
  return (
    <AppShell
      navbar={{ width: 300, breakpoint: "sm" }}
      padding={{ base: 10, sm: 15, lg: "xl" }}
    >
      <AppShell.Navbar>chats go here</AppShell.Navbar>
      <AppShellMain>chat go here</AppShellMain>
    </AppShell>
  );
}

export default App;
