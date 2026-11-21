const BASE = import.meta.env.VITE_API_BASE ?? "/api";
let token = sessionStorage.getItem("token");
let onUnauthorized = () => {};

export function setToken(t) {
  token = t;
  if (t) sessionStorage.setItem("token", t);
  else sessionStorage.removeItem("token");
}
export const hasToken = () => Boolean(token);
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function describe(data) {
  const d = data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((e) => `${e.loc.slice(1).join(".")}: ${e.msg}`).join("; ");
  return "Something went wrong. Try again.";
}

async function call(path, { method = "GET", body, auth = true } = {}) {
  let res;
  try {
    res = await fetch(BASE + path, {
      method,
      headers: {
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check your connection and try again.");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && auth) onUnauthorized();
    throw new ApiError(res.status, describe(data));
  }
  return data;
}

export const api = {
  login: (email, password) => call("/auth/login", { method: "POST", body: { email, password }, auth: false }),
  me: () => call("/auth/me"),
  listRequests: (status) => call(`/requests${status ? `?status=${status}` : ""}`),
  getRequest: (id) => call(`/requests/${id}`),
  createRequest: (body) => call("/requests", { method: "POST", body }),
  review: (id) => call(`/requests/${id}/review`, { method: "POST" }),
  decide: (id, body) => call(`/requests/${id}/decision`, { method: "POST", body }),
  dashboard: () => call("/dashboard"),
  metrics: () => call("/metrics"),
  policies: () => call("/policies"),
  createPolicy: (body) => call("/policies", { method: "POST", body }),
  users: () => call("/users"),
  createUser: (body) => call("/auth/register", { method: "POST", body }),
  audit: () => call("/audit?limit=100"),
};
