import { useEffect, useState } from "react";
import { getHealth } from "../api/client.js";

export default function HealthBadge() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        const data = await getHealth();
        if (alive) setStatus(data.status === "ok" ? "online" : "error");
      } catch {
        if (alive) setStatus("offline");
      }
    };
    check();
    const timer = setInterval(check, 15000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  const config = {
    checking: { color: "bg-slate-500", text: "Checking API…", pulse: true },
    online: { color: "bg-emerald-400", text: "API online", pulse: false },
    offline: { color: "bg-red-400", text: "API offline", pulse: false },
    error: { color: "bg-amber-400", text: "API degraded", pulse: false },
  }[status];

  return (
    <div className="flex items-center gap-2 rounded-full border border-junction-line bg-junction-panel2 px-3 py-1.5">
      <span
        className={`relative inline-flex h-2.5 w-2.5 ${config.color} rounded-full ${
          config.pulse ? "animate-pulse" : ""
        }`}
      />
      <span className="text-xs font-medium text-slate-300">{config.text}</span>
    </div>
  );
}