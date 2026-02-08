import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? "http://localhost:8000",
});

export const authFetch = async (url: string, token: string) => {
  try {
    const resp = await api.get(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    
    // Return a fetch-like response object
    return {
      ok: true,
      status: resp.status,
      statusText: resp.statusText,
      json: async () => resp.data
    };
  } catch (error: any) {
    // Return a fetch-like error response
    return {
      ok: false,
      status: error.response?.status || 0,
      statusText: error.response?.statusText || error.message,
      json: async () => error.response?.data || {}
    };
  }
};

export const postAuth = async (url: string, body: unknown, token: string) => {
  try {
    const resp = await api.post(url, body, {
      headers: { Authorization: `Bearer ${token}` },
    });
    
    // Return a fetch-like response object  
    return {
      ok: true,
      status: resp.status,
      statusText: resp.statusText,
      json: async () => resp.data
    };
  } catch (error: any) {
    // Return a fetch-like error response
    return {
      ok: false,
      status: error.response?.status || 0,
      statusText: error.response?.statusText || error.message,
      json: async () => error.response?.data || {}
    };
  }
};

export const deleteAuth = async (url: string, token: string) => {
  try {
    const resp = await api.delete(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    
    // Return a fetch-like response object
    return {
      ok: true,
      status: resp.status,
      statusText: resp.statusText,
      json: async () => resp.data
    };
  } catch (error: any) {
    // Return a fetch-like error response
    return {
      ok: false,
      status: error.response?.status || 0,
      statusText: error.response?.statusText || error.message,
      json: async () => error.response?.data || {},
      text: async () => error.response?.statusText || error.message
    };
  }
};
