import { lazy, Suspense } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import ErrorBoundary from "@/components/ErrorBoundary";
import { OfflineBanner } from "@/components/OfflineBanner";
import { LoadingScreen } from "@/components/LoadingScreen";
import { queryClient } from "@/lib/queryClient";

// Lazy load all pages for code splitting (FAANG-level performance)
const Landing = lazy(() => import("./pages/Landing"));
const SignUp = lazy(() => import("./pages/SignUp"));
const Login = lazy(() => import("./pages/Login"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const Onboarding = lazy(() => import("./pages/Onboarding"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const OpportunityDetail = lazy(() => import("./pages/OpportunityDetail"));
const SavedOpportunities = lazy(() => import("./pages/SavedOpportunities"));
const Apply = lazy(() => import("./pages/Apply"));
const Applications = lazy(() => import("./pages/Applications"));
const ApplicationTracker = lazy(() => import("./pages/ApplicationTracker"));
const Profile = lazy(() => import("./pages/Profile"));
const NotFound = lazy(() => import("./pages/NotFound"));

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <div className="dark min-h-screen bg-background text-foreground">
            <OfflineBanner />
            <Toaster />
            <Sonner />
            <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
              <Suspense fallback={<LoadingScreen />}>
                <Routes>
                  <Route path="/" element={<Landing />} />
                  <Route path="/signup" element={<SignUp />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/forgot-password" element={<ForgotPassword />} />
                  <Route
                    path="/onboarding"
                    element={
                      <ProtectedRoute requireOnboarding={false}>
                        <Onboarding />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/dashboard"
                    element={
                      <ProtectedRoute>
                        <Dashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/opportunity/:id"
                    element={
                      <ProtectedRoute>
                        <OpportunityDetail />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/saved"
                    element={
                      <ProtectedRoute>
                        <SavedOpportunities />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/apply/:scholarshipId"
                    element={
                      <ProtectedRoute>
                        <Apply />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/applications"
                    element={
                      <ProtectedRoute>
                        <Applications />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/application-tracker"
                    element={
                      <ProtectedRoute>
                        <ApplicationTracker />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/profile"
                    element={
                      <ProtectedRoute>
                        <Profile />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Suspense>
            </BrowserRouter>
          </div>
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;