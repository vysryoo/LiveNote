import { createRoot } from "react-dom/client";
import App from "./legacy/App.tsx";
import "./styles/globals.css";
import { BackendProvider } from "./legacy/services/BackendContext";
import { I18nProvider } from "./legacy/i18n/I18nContext";

createRoot(document.getElementById("root")!).render(
  <BackendProvider>
    <I18nProvider>
      <App />
    </I18nProvider>
  </BackendProvider>,
);
