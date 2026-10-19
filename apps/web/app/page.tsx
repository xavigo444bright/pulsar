"use client";

import { CSSProperties, FormEvent, useCallback, useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Msg = { role: "user" | "assistant"; text: string; tool?: string };

export default function Page() {
  const [overview, setOverview] = useState<any>(null);
  const [error, setError] = useState<string>("");
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      text: "Pulsar 默认纸交易。问我「开始研究」「为什么没晋升」「风控」或「停机」。主网不会从聊天打开。",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/v1/overview`);
      if (!res.ok) throw new Error(`overview ${res.status}`);
      setOverview(await res.json());
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "API unreachable");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, [refresh]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    setMessages((m) => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const res = await fetch(`${API}/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", text: data.reply || JSON.stringify(data), tool: data.tool }]);
      await refresh();
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: String(err) }]);
    } finally {
      setBusy(false);
    }
  }

  const kill = overview?.kill;
  const board: any[] = overview?.board || [];
  const accounts: any[] = overview?.accounts || [];
  const positions: any[] = overview?.positions || [];
  const evaluations: any[] = overview?.evaluations || [];
  const audit: any[] = overview?.audit || [];

  const evalRows = useMemo(() => {
    return evaluations.slice(0, 12).map((row) => {
      let metrics: any = {};
      try {
        metrics = typeof row.metrics === "string" ? JSON.parse(row.metrics) : row.metrics;
      } catch {
        metrics = {};
      }
      return { ...row, metrics };
    });
  }, [evaluations]);

  return (
    <main style={shell}>
      <header style={topbar}>
        <div>
          <div style={brand}>PULSAR</div>
          <div style={sub}>RSI-gated agent · paper by default · not financial advice</div>
        </div>
        <div style={pills}>
          <Pill ok={!overview?.live_enabled} label={overview?.live_enabled ? "LIVE ON" : "LIVE OFF"} />
          <Pill ok={!kill?.tripped} label={kill?.tripped ? `KILL ${kill.reason}` : "KILL ARMED"} />
          <Pill ok label={(overview?.decision_backend || "rules").toUpperCase()} />
        </div>
      </header>
      {error ? <div style={banner}>API {error}. 先运行 pulsar serve</div> : null}
      <section style={grid}>
        <aside style={chatCol}>
          <div style={colTitle}>对话</div>
          <div style={log}>
            {messages.map((m, i) => (
              <div key={i} style={m.role === "user" ? userBubble : botBubble}>
                {m.tool ? <div style={toolTag}>{m.tool}</div> : null}
                <pre style={pre}>{m.text}</pre>
              </div>
            ))}
          </div>
          <form onSubmit={onSubmit} style={form}>
            <input
              style={input}
              value={draft}
              placeholder="开始研究 / 为什么没晋升 / 停机"
              onChange={(e) => setDraft(e.target.value)}
            />
            <button style={btn} disabled={busy} type="submit">
              {busy ? "…" : "发送"}
            </button>
          </form>
        </aside>
        <section style={dash}>
          <div style={colTitle}>监控与审计</div>
          <div style={cards}>
            {accounts.map((a) => (
              <article key={a.market_id} style={card}>
                <div style={muted}>{a.market_id}</div>
                <div style={big}>{Number(a.equity).toFixed(2)}</div>
                <div style={muted}>
                  {a.mode} · cash {Number(a.cash).toFixed(2)}
                </div>
              </article>
            ))}
          </div>
          <h2 style={h2}>晋升榜</h2>
          <table style={table}>
            <thead>
              <tr>
                <th>因子</th>
                <th>状态</th>
                <th>原因</th>
              </tr>
            </thead>
            <tbody>
              {board.length === 0 ? (
                <tr>
                  <td colSpan={3} style={muted}>
                    还没有研究循环。在左侧说「开始研究」。
                  </td>
                </tr>
              ) : (
                board.map((row) => (
                  <tr key={row.factor_id}>
                    <td>
                      <code>{row.factor_id}</code>
                      <div style={muted}>{row.name}</div>
                    </td>
                    <td style={{ color: row.state === "paper" ? "var(--green)" : row.state === "rejected" ? "var(--red)" : "var(--gold)" }}>
                      {row.state}
                    </td>
                    <td style={muted}>{row.reason}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <h2 style={h2}>持仓</h2>
          <table style={table}>
            <thead>
              <tr>
                <th>市场</th>
                <th>标的</th>
                <th>数量</th>
                <th>均价</th>
              </tr>
            </thead>
            <tbody>
              {positions.length === 0 ? (
                <tr>
                  <td colSpan={4} style={muted}>
                    空仓
                  </td>
                </tr>
              ) : (
                positions.map((p, i) => (
                  <tr key={i}>
                    <td>{p.market_id}</td>
                    <td>{p.symbol}</td>
                    <td>{p.quantity}</td>
                    <td>{Number(p.avg_price).toFixed(4)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <h2 style={h2}>门控指标</h2>
          <table style={table}>
            <thead>
              <tr>
                <th>因子</th>
                <th>市场</th>
                <th>Sharpe</th>
                <th>超额</th>
                <th>过门</th>
              </tr>
            </thead>
            <tbody>
              {evalRows.map((row, i) => (
                <tr key={i}>
                  <td>
                    <code>{row.factor_id}</code>
                  </td>
                  <td>
                    {row.market_id}/{row.symbol}
                  </td>
                  <td>{Number(row.metrics.sharpe || 0).toFixed(2)}</td>
                  <td>{Number(row.metrics.excess_sharpe || 0).toFixed(2)}</td>
                  <td style={{ color: row.passed ? "var(--green)" : "var(--red)" }}>{row.passed ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h2 style={h2}>审计</h2>
          <div style={auditBox}>
            {audit.slice(0, 12).map((row, i) => (
              <div key={i} style={auditLine}>
                <span style={muted}>{row.ts}</span> {row.actor} {row.action}
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

function Pill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      style={{
        border: `1px solid ${ok ? "var(--green)" : "var(--red)"}`,
        color: ok ? "var(--green)" : "var(--red)",
        padding: "4px 10px",
        borderRadius: 999,
        fontFamily: "IBM Plex Mono, ui-monospace, monospace",
        fontSize: 12,
      }}
    >
      {label}
    </span>
  );
}

const shell: CSSProperties = { minHeight: "100%", background: "radial-gradient(1200px 500px at 10% -10%, #1a1408 0%, #07090d 45%)" };
const topbar: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "20px 24px",
  borderBottom: "1px solid var(--line)",
};
const brand: CSSProperties = {
  fontFamily: "IBM Plex Mono, ui-monospace, monospace",
  color: "var(--gold)",
  letterSpacing: "0.28em",
  fontWeight: 500,
};
const sub: CSSProperties = { color: "var(--muted)", fontSize: 12, marginTop: 4 };
const pills: CSSProperties = { display: "flex", gap: 8, flexWrap: "wrap" };
const banner: CSSProperties = { margin: 16, padding: 12, border: "1px solid var(--red)", color: "var(--red)" };
const grid: CSSProperties = { display: "grid", gridTemplateColumns: "minmax(320px, 420px) 1fr", minHeight: "calc(100vh - 88px)" };
const chatCol: CSSProperties = { borderRight: "1px solid var(--line)", display: "flex", flexDirection: "column", background: "var(--bg-2)" };
const dash: CSSProperties = { padding: 20, overflow: "auto" };
const colTitle: CSSProperties = {
  padding: "14px 16px",
  color: "var(--gold)",
  fontFamily: "IBM Plex Mono, ui-monospace, monospace",
  letterSpacing: "0.14em",
  fontSize: 12,
};
const log: CSSProperties = { flex: 1, overflow: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 12 };
const userBubble: CSSProperties = { alignSelf: "flex-end", background: "#1c2430", padding: 12, borderRadius: 12, maxWidth: "92%" };
const botBubble: CSSProperties = { alignSelf: "flex-start", background: "#16120c", border: "1px solid var(--line)", padding: 12, borderRadius: 12, maxWidth: "92%" };
const pre: CSSProperties = { margin: 0, whiteSpace: "pre-wrap", fontFamily: "IBM Plex Sans, sans-serif", fontSize: 14 };
const toolTag: CSSProperties = { color: "var(--gold)", fontSize: 11, fontFamily: "IBM Plex Mono, monospace", marginBottom: 6 };
const form: CSSProperties = { display: "flex", gap: 8, padding: 12, borderTop: "1px solid var(--line)" };
const input: CSSProperties = { flex: 1, background: "#0b0f14", border: "1px solid var(--line)", padding: "10px 12px", borderRadius: 8 };
const btn: CSSProperties = { background: "var(--gold)", color: "#111", border: 0, padding: "10px 16px", borderRadius: 8, fontWeight: 600 };
const cards: CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 };
const card: CSSProperties = { background: "var(--panel)", border: "1px solid var(--line)", padding: 14, borderRadius: 12 };
const muted: CSSProperties = { color: "var(--muted)", fontSize: 12 };
const big: CSSProperties = { fontFamily: "IBM Plex Mono, monospace", fontSize: 22, margin: "6px 0" };
const h2: CSSProperties = { fontSize: 13, letterSpacing: "0.12em", color: "var(--gold)", margin: "22px 0 8px", fontFamily: "IBM Plex Mono, monospace" };
const table: CSSProperties = { width: "100%", borderCollapse: "collapse", fontSize: 13 };
const auditBox: CSSProperties = { fontFamily: "IBM Plex Mono, monospace", fontSize: 12, color: "var(--muted)" };
const auditLine: CSSProperties = { padding: "4px 0", borderBottom: "1px solid #1b2230" };
