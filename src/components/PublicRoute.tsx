import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { LoadingScreen } from "@/components/LoadingScreen";

interface PublicRouteProps {
    children: React.ReactNode;
}

export const PublicRoute = ({ children }: PublicRouteProps) => {
    const { user, loading } = useAuth(); // Assuming useAuth exposes loading state

    if (loading) {
        return <LoadingScreen />;
    }

    if (user) {
        // If user is authenticated, redirect to dashboard
        return <Navigate to="/dashboard" replace />;
    }

    // If not authenticated, render the children (Login/SignUp/Landing)
    return <>{children}</>;
};
