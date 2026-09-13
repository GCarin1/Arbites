import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AuthGate } from "./components/AuthGate";
import { ToastProvider } from "./components/Toast";
import { applyDensity, loadDensity } from "./density";
import { applyTheme, loadTheme } from "./theme";
import "./styles.css";

// Antes da primeira pintura: a tela não pode aparecer numa densidade ou num
// tema e pular para outro quando o React montar.
applyDensity(loadDensity());
applyTheme(loadTheme());

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ToastProvider>
      <AuthGate>
        {(user, logout) => <App user={user} onLogout={logout} />}
      </AuthGate>
    </ToastProvider>
  </React.StrictMode>,
);
