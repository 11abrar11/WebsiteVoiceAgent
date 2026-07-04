/**
 * React Entry Point
 * - Boots up the React application
 * - Mounts the App component to the 'root' div in index.html
 * - Wraps with HelmetProvider for per-page SEO meta tag management
 */
import { createRoot } from "react-dom/client";
import { HelmetProvider } from "react-helmet-async";
import App from "./App";
import "./index.css"; // Global styles and Tailwind imports

// Create the concurrent React root and render the application
createRoot(document.getElementById("root")!).render(
  <HelmetProvider>
    <App />
  </HelmetProvider>
);
