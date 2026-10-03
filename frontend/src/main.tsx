import { createRoot } from "react-dom/client";
import "./shared/i18n";
import "./styles/globals.css";
import { App } from "./app/App";

createRoot(document.getElementById("root")!).render(<App />);
