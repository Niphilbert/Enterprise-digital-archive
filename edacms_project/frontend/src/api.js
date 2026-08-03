import axios from "axios";

const API_BASE = "http://127.0.0.1:5000/api";

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("edacms_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem("edacms_token");
      localStorage.removeItem("edacms_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
export { API_BASE };
