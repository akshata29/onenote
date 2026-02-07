import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? "http://localhost:8000",
});

export const authFetch = async <T>(url: string, token: string) => {
  const resp = await api.get<T>(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return resp.data;
};

export const postAuth = async <T>(url: string, body: unknown, token: string) => {
  const resp = await api.post<T>(url, body, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return resp.data;
};
