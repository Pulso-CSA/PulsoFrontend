import { createRoot } from "react-dom/client";
import "./i18n";
import App from "./App.tsx";
import "./index.css";
import "./styles/components-showcase.css";
import "./styles/cosmic-search.css";

createRoot(document.getElementById("root")!).render(
  <div className="flex h-full min-h-0 flex-col">
    <App />
  </div>,
);
