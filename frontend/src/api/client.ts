// Axios client. Adds the X-User-Id header automatically based on
// what is in localStorage (set by the Login page).

import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
});

// Before every request, attach the current user id from localStorage.
api.interceptors.request.use((config) => {
  const userId = localStorage.getItem("skynet_user_id");
  if (userId) {
    config.headers["X-User-Id"] = userId;
  }
  return config;
});
