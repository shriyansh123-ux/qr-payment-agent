import { useEffect, useState } from "react";
import "./App.css";
import { getConfig } from "./lib/api";
import AccountPanel from "./components/AccountPanel";
import CashHelper from "./components/CashHelper";
import CurrencyConverter from "./components/CurrencyConverter";
import QRDemo from "./components/QRDemo";

const WORKSPACES = [
  ["demo", "QR demo"],
  ["account", "Saved scans"],
  ["converter", "Currency converter"],
  ["cash", "Cash helper"],
];

export default function App() {
  const [workspace, setWorkspace] = useState("demo");
  // Shared by the QR demo and converter; kept in memory only.
  const [apiKey, setApiKey] = useState("");
  const [publicDemo, setPublicDemo] = useState(false);

  useEffect(() => {
    let alive = true;
    getConfig().then(config => { if (alive) setPublicDemo(config.public_demo === true); })
      .catch(() => { /* Older servers have no /api/config: behave as key-required. */ });
    return () => { alive = false; };
  }, []);

  return (
    <div className="page">
      <div className="container">
        <h1 className="title">Travel QR Cost Estimator</h1>
        <p className="subtitle">
          Estimate costs from supported QRs, explore fees, and check cash payments in a supported local currency. No payments are made here.
        </p>
        <div className="tabs" role="group" aria-label="Workspace">
          {WORKSPACES.map(([value, label]) => <button key={value} type="button"
            className={`tab ${workspace === value ? "active" : ""}`} onClick={() => setWorkspace(value)}>{label}</button>)}
        </div>
        {workspace === "cash" && <CashHelper />}
        {workspace === "account" && <AccountPanel />}
        {workspace === "converter" && <CurrencyConverter apiKey={apiKey} onApiKeyChange={setApiKey} publicDemo={publicDemo} />}
        {/* Kept mounted so the demo's in-page history survives switching tabs. */}
        <div hidden={workspace !== "demo"}>
          <QRDemo apiKey={apiKey} onApiKeyChange={setApiKey} publicDemo={publicDemo} />
        </div>
      </div>
    </div>
  );
}
