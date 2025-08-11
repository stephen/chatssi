import { AppShell, AppShellMain, Button, LoadingOverlay } from "@mantine/core";
import { useEffect, useState } from "react";
import { Route, Switch, useLocation } from "wouter";
import { authGetMe, type UserSchema } from "./api-client";
import { client } from "./api-client/client.gen";
import "./App.css";
import AuthCallback from "./AuthCallback";
import Chat from "./Chat";
import NewChat from "./NewChat";
import { State, useSimpleState } from "./SimpleState";

client.setConfig({
  baseUrl: "/api/",
  throwOnError: true,
});

const user = new State<UserSchema | null>(null);

function Dashboard() {
  const [, navigate] = useLocation();

  const handleLogout = async () => {
    await fetch("/api/auth/logout");
    user.set(null);
    window.location.reload(); // Refresh to ensure clean state
  };

  const [u] = useSimpleState(user);

  return (
    <AppShell
      navbar={{ width: 300, breakpoint: "sm" }}
      padding={{ base: 10, sm: 15, lg: "xl" }}
    >
      <AppShell.Navbar>
        <div style={{ padding: "15px" }}>
          <p>Welcome, {u.name}!</p>
          <Button size="sm" variant="outline" onClick={handleLogout}>
            Sign out
          </Button>
          <hr />
          <Button
            size="sm"
            variant="filled"
            onClick={() => navigate("/new")}
            mb="md"
          >
            New Chat
          </Button>
        </div>
      </AppShell.Navbar>
      <AppShellMain>
        <Switch>
          <Route path="/new" component={NewChat} />
          <Route path="/chats/:id" component={Chat} />
        </Switch>
      </AppShellMain>
    </AppShell>
  );
}

function Login() {
  return (
    <div style={{ padding: "50px", textAlign: "center" }}>
      <h1>Welcome to ChatSSI</h1>
      <Button onClick={() => (window.location.href = "/api/auth/login")}>
        Sign in with Google
      </Button>
    </div>
  );
}

function AuthenticatedApp() {
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    (async () => {
      try {
        const userData = await authGetMe();
        if (userData.data) {
          user.set(userData.data);
        }
      } catch (err: unknown) {
        console.log("Not authenticated:", err);
        window.location.href = "/login";
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

  if (!loaded) {
    return <LoadingOverlay />;
  }

  return (
    <Switch>
      <Route component={Dashboard} />
    </Switch>
  );
}

function App() {
  return (
    <Switch>
      <Route path="/login" component={Login} />
      <Route path="/auth/callback" component={AuthCallback} />
      <Route component={AuthenticatedApp} />
    </Switch>
  );
}

export default App;
