/**
 * Main Application Component
 * - Configures Global Providers (Tooltip, Toaster)
 * - Defines the Client-Side Router and Page Transitions
 */
import { Switch, Route } from "wouter";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import { ScrollToTop } from "@/components/ScrollToTop";
import { Suspense, lazy } from "react";
import { Loader2 } from "lucide-react";

// Standard Pages (Eagerly loaded for instant access)
import Home from "@/pages/Home";
import Services from "@/pages/Services";
import Portfolio from "@/pages/Portfolio";
import About from "@/pages/About";
import Contact from "@/pages/Contact";
import VoiceAgent from "@/pages/VoiceAgent";
import AdminLogin from "@/pages/AdminLogin";
import AdminDashboard from "@/pages/AdminDashboard";

/**
 * Lazy-loaded Pages
 * Components that are large are loaded only when the user navigates to them
 * to improve initial page load speed.
 */
const CaseStudyDetail = lazy(() => import("@/pages/CaseStudyDetail"));

/**
 * Router Component
 * Manages the URL paths and which page component to display.
 */
function Router() {
  return (
    <>
      {/* Ensures the window scrolls to top on every navigation */}
      <ScrollToTop />

      <Switch>
        <Route path="/" component={Home} />
        <Route path="/services" component={Services} />
        <Route path="/portfolio" component={Portfolio} />
        <Route path="/about" component={About} />
        <Route path="/contact" component={Contact} />
        <Route path="/voice-agent" component={VoiceAgent} />
        <Route path="/voice-agent/admin" component={AdminLogin} />
        <Route path="/voice-agent/admin/dashboard" component={AdminDashboard} />

        {/* Dynamic Route for Project Details */}
        <Route path="/case-study/:slug" component={() => (
          <Suspense fallback={
            <div className="flex justify-center pt-20">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          }>
            <CaseStudyDetail />
          </Suspense>
        )} />

        {/* Fallback for 404 - Not Found */}
        <Route component={NotFound} />
      </Switch>
    </>
  );
}

/**
 * Root App Component
 * Wraps the Router with all necessary context providers.
 */
function App() {
  return (
    /* enables hover tooltips across the app */
    <TooltipProvider>
      {/* enables toast notifications (popups) */}
      <Toaster />
      <Router />
    </TooltipProvider>
  );
}

export default App;

