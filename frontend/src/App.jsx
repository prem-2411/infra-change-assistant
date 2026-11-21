import { useCallback, useEffect, useRef, useState } from "react";
import { api, hasToken, setToken, setUnauthorizedHandler } from "./api.js";
import Admin from "./pages/Admin.jsx";
import Insights from "./pages/Insights.jsx";
import Login from "./pages/Login.jsx";
import RequestDetail from "./pages/RequestDetail.jsx";
import RequestForm from "./pages/RequestForm.jsx";
import RequestList from "./pages/RequestList.jsx";

const NAV = {
  engineer: [["list", "My requests"], ["new", "New request"]],
  approver: [["list", "Approval queue"], ["insights", "Dashboard"]],
  admin: [["list", "All requests"], ["insights", "Dashboard"], ["admin", "Administration"]],
};

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(hasToken());
  const [view, setView] = useState({ name: "list" });
  const mainRef = useRef(null);

  const signOut = useCallback(() => {
    setToken(null);
    setUser(null);
    setView({ name: "list" });
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(signOut);
    if (!hasToken()) return;
    api.me().then(setUser).catch(() => {}).finally(() => setBooting(false));
  }, [signOut]);

  // Move focus to the new page so keyboard and screen-reader users know the view changed.
  useEffect(() => { mainRef.current?.focus(); }, [view]);

  const go = (name, id) => setView({ name, id });

  if (booting) return <p className="boot" role="status">Loading…</p>;
  if (!user) return <Login onLogin={(u) => { setUser(u); go("list"); }} />;

  return (
    <>
      <a className="skip" href="#main">Skip to main content</a>
      <header className="bar">
        <p className="brand">Infra Change Assistant</p>
        <nav aria-label="Main">
          {NAV[user.role].map(([name, label]) => (
            <button key={name} className="navlink" aria-current={view.name === name ? "page" : undefined}
                    onClick={() => go(name)}>{label}</button>
          ))}
        </nav>
        <div className="who">
          <span>{user.name} ({user.role})</span>
          <button className="linklike" onClick={signOut}>Sign out</button>
        </div>
      </header>
      <main id="main" tabIndex={-1} ref={mainRef}>
        {view.name === "list" && <RequestList user={user} onOpen={(id) => go("detail", id)} />}
        {view.name === "new" && <RequestForm onCreated={(id) => go("detail", id)} />}
        {view.name === "detail" && <RequestDetail id={view.id} user={user} onBack={() => go("list")} />}
        {view.name === "insights" && <Insights user={user} />}
        {view.name === "admin" && <Admin />}
      </main>
    </>
  );
}
