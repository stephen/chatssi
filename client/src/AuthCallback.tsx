import { useEffect } from "react";
import { authCallback } from "./api-client";

export default function AuthCallback() {
  useEffect(() => {
    const handleCallback = async () => {
      // Get the authorization code from URL params
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get("code");
      const error = urlParams.get("error");

      if (error) {
        window.location.href = "/";
        return;
      }

      if (!code) {
        window.location.href = "/";
        return;
      }

      try {
        const response = await authCallback({
          body: { code },
          throwOnError: true,
        });

        console.log("Authentication successful:", response.data);

        // Redirect to home/dashboard
        window.location.href = "/";
      } catch (error: unknown) {
        console.error("Authentication failed:", error);
        alert(
          "Authentication failed: " +
            (error?.detail || error?.message || "Unknown error")
        );
        window.location.href = "/";
      }
    };

    handleCallback();
  }, []);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            width: "50px",
            height: "50px",
            border: "5px solid #f3f3f3",
            borderTop: "5px solid #3498db",
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
            margin: "0 auto 20px",
          }}
        />
        <h2>Authenticating...</h2>
        <p>Please wait while we complete your sign-in.</p>
      </div>
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
}
