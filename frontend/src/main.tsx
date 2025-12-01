
  import { createRoot } from "react-dom/client";
  import App from "./App.tsx";
  import "./index.css";
  import { BackendProvider } from "./services/BackendContext";
  import { I18nProvider } from "./i18n/I18nContext";

  createRoot(document.getElementById("root")!).render(
    <BackendProvider>
      <I18nProvider>
        <App />
      </I18nProvider>
    </BackendProvider>
  );
  
  