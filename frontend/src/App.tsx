import { useEffect, useMemo, useState } from "react";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import useSWR, { mutate } from "swr";
import { authFetch, postAuth } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { Sidebar } from "./components/Sidebar";
import { AdminPanel } from "./components/AdminPanel";

export type Mode = "mcp" | "search" | "admin";

function useAccessToken(): string | null {
  const { instance, accounts } = useMsal();
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    const acct = accounts[0];
    if (!acct) {
      console.log("No account found");
      return;
    }
    
    // Wait a bit to ensure MSAL is fully initialized
    setTimeout(async () => {
      console.log("Acquiring token for account:", acct.username);
      try {
        const resp = await instance.acquireTokenSilent({
          scopes: [import.meta.env.VITE_API_SCOPE || "api://your-api-app-id/access_as_user"],
          account: acct,
        });
        console.log("Token acquired silently");
        setToken(resp.accessToken);
      } catch (error) {
        console.log("Silent token acquisition failed:", error);
        try {
          const resp = await instance.acquireTokenPopup({ scopes: [import.meta.env.VITE_API_SCOPE || "api://your-api-app-id/access_as_user"] });
          console.log("Token acquired via popup");
          setToken(resp.accessToken);
        } catch (popupError) {
          console.error("Popup token acquisition failed:", popupError);
        }
      }
    }, 100);
  }, [accounts, instance]);
  return token;
}

const skeleton = <div className="text-slate-300">Loading...</div>;

export default function App() {
  const isAuth = useIsAuthenticated();
  const { instance } = useMsal();
  const token = useAccessToken();
  const [mode, setMode] = useState<Mode>("search");
  const [scope, setScope] = useState<{ notebook?: string; section?: string; page?: string }>({});
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Manual refresh function for when needed
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    try {
      await mutate('/notebooks');
      if (scope.notebook) await mutate(`/notebooks/${scope.notebook}/sections`);
      if (scope.section) await mutate(`/sections/${scope.section}/pages`);
    } catch (error) {
      console.error('Manual refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const fetcher = async (url: string) => {
    if (!token) throw new Error("no token yet");
    
    try {
      const response = await authFetch(url, token);
      
      // Handle rate limiting gracefully
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : 30000;
        throw new Error(`Rate limited. Retry after ${waitTime}ms`);
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      console.error('Fetch error for', url, ':', error);
      throw error;
    }
  };

  const { data: notebooks, error: notebooksError } = useSWR(token ? "/notebooks" : null, fetcher, {
    // Only revalidate notebooks when explicitly requested
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    // Cache for 5 minutes
    dedupingInterval: 300000,
  });
  
  const { data: sections, error: sectionsError } = useSWR(scope.notebook ? `/notebooks/${scope.notebook}/sections` : null, fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    dedupingInterval: 300000,
  });
  
  const { data: pages, error: pagesError } = useSWR(scope.section ? `/sections/${scope.section}/pages` : null, fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    dedupingInterval: 300000,
  });

  if (!isAuth) {
    return (
      <main className="min-h-screen flex items-center justify-center text-slate-100">
        <div className="bg-panel border border-slate-700 rounded-2xl p-8 shadow-2xl max-w-md w-full">
          <h1 className="text-2xl font-semibold mb-4">OneNote RAG</h1>
          <p className="text-slate-300 mb-6">Sign in with your work account to chat over OneNote.</p>
          <button
            onClick={() => instance.loginPopup({ scopes: [import.meta.env.VITE_API_SCOPE || "api://your-api-app-id/access_as_user", "User.Read", "Notes.Read"] })}
            className="w-full py-3 bg-accent text-slate-950 font-semibold rounded-lg"
          >
            Sign in with Entra ID
          </button>
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen grid grid-cols-[280px_1fr] text-slate-100">
      <Sidebar
        mode={mode}
        onModeChange={setMode}
        notebooks={notebooks?.value || []}
        sections={sections?.value || []}
        pages={pages?.value || []}
        scope={scope}
        onScopeChange={setScope}
        onRefresh={handleManualRefresh}
        isRefreshing={isRefreshing}
        errors={{
          notebooks: notebooksError,
          sections: sectionsError,
          pages: pagesError
        }}
      />
      
      {/* Main Content Area */}
      {mode === "admin" ? (
        <AdminPanel 
          token={token} 
          notebooks={notebooks?.value || []} 
        />
      ) : (
        <ChatPanel 
          mode={mode} 
          scope={scope} 
          token={token} 
          notebooks={notebooks?.value || []}
        />
      )}
    </div>
  );
}
