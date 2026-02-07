import React from "react";
import ReactDOM from "react-dom/client";
import { MsalProvider } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";
import App from "./App";
import "./styles.css";

const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_CLIENT_ID ?? "",
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
        <App />
      </MsalProvider>
    </React.StrictMode>
  );
});
