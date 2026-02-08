import React from "react";
import ReactDOM from "react-dom/client";
import { MsalProvider } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";
import { SWRConfig } from "swr";
import App from "./App";
import "./styles.css";

const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_CLIENT_ID || "",
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_TENANT_ID}`,
    redirectUri: window.location.origin,
  },
};

const pca = new PublicClientApplication(msalConfig);

// Initialize MSAL before rendering
pca.initialize().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <MsalProvider instance={pca}>
        <SWRConfig value={{
          // Cache for 5 minutes to reduce API calls
          dedupingInterval: 300000, // 5 minutes
          // Don't refetch on window focus to avoid excessive requests
          revalidateOnFocus: false,
          // Don't refetch on network reconnect immediately
          revalidateOnReconnect: false,
          // Disable automatic revalidation interval
          refreshInterval: 0,
          // Keep data fresh for 5 minutes
          focusThrottleInterval: 300000,
          // Retry with exponential backoff
          errorRetryInterval: 5000,
          errorRetryCount: 3,
          // Custom retry logic for rate limits
          onErrorRetry: (error, key, config, revalidate, { retryCount }) => {
            // Don't retry on 4xx errors (except 429)
            if (error.message.includes('status: 4') && !error.message.includes('429')) return;
            
            // Stop after 3 retries
            if (retryCount >= 3) return;
            
            // Exponential backoff for rate limits
            const timeout = error.message.includes('429') 
              ? Math.min(30000, 1000 * Math.pow(2, retryCount)) // 1s, 2s, 4s for 429s
              : 5000; // 5s for other errors
              
            setTimeout(() => revalidate({ retryCount }), timeout);
          }
        }}>
          <App />
        </SWRConfig>
      </MsalProvider>
    </React.StrictMode>
  );
});
