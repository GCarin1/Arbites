import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AuthGate } from "./components/AuthGate";
import { ToastProvider } from "./components/Toast";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ToastProvider>
      <AuthGate>
        {(user, logout) => <App user={user} onLogout={logout} />}
      </AuthGate>
    </ToastProvider>
  </React.StrictMode>,
);
