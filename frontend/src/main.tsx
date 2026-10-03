import { createRoot } from "react-dom/client";
import "./shared/i18n";
import App from "./legacy/App.tsx";
import "./styles/globals.css";
import { BackendProvider } from "./legacy/services/BackendContext";

createRoot(document.getElementById("root")!).render(
  <BackendProvider>
    <App />
  </BackendProvider>,
);
