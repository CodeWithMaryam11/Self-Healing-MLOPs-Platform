import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './views/Login';
import { Register } from './views/Register';
import { DashboardOverview } from './views/DashboardOverview';
import { useAuthStore } from './stores/useAuthStore';
import { Terminal, LogOut, ShieldCheck, User } from 'lucide-react';

// Configure TanStack Query Client with optimal defaults for live MLOps polling
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true,
      retry: 2,
      staleTime: 4000,
    },
  },
});

const NavigationHeader = () => {
  const { user, isAuthenticated, logout } = useAuthStore();

  if (!isAuthenticated) return null;

  return (
    <header className="bg-zinc-50 border-b border-zinc-300/80 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="p-1.5 bg-white border border-zinc-200 text-indigo-600 group-hover:border-indigo-600 transition-colors">
              <Terminal className="w-5 h-5" />
            </div>
            <span className="font-mono font-bold tracking-wider text-lg text-zinc-900">PIPELINEIQ</span>
          </Link>
          <span className="hidden sm:inline-block text-[10px] font-mono uppercase bg-white border border-zinc-200 text-zinc-400 px-2 py-0.5">
            Principal MLOps Telemetry
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 font-mono text-xs text-zinc-400 bg-white/80 px-3 py-1.5 border border-zinc-200">
            <ShieldCheck className="w-3.5 h-3.5 text-green-500" />
            <span>FastAPI REST Connected</span>
          </div>

          <div className="flex items-center gap-3 pl-4 border-l border-zinc-200">
            <div className="flex items-center gap-2 text-xs font-mono text-zinc-700">
              <User className="w-4 h-4 text-zinc-500" />
              <span>{user?.email || 'operator@pipelineiq.ml'}</span>
            </div>
            <button
              onClick={logout}
              title="Terminate Session"
              className="p-1.5 bg-white hover:bg-red-50 hover:text-red-600 border border-zinc-200 hover:border-red-200 text-zinc-400 transition-all cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-zinc-50 text-zinc-900 flex flex-col font-sans">
          <NavigationHeader />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <DashboardOverview />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
          
          <footer className="border-t border-zinc-900 py-6 text-center text-[11px] font-mono text-zinc-400">
            PIPELINEIQ // INDUSTRIAL MLOPS TELEMETRY SYSTEM // FASTAPI + ZUSTAND + TANSTACK QUERY
          </footer>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
