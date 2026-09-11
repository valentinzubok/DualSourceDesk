"use client";

import { useCallback, useEffect, useState } from "react";
import { DEMO_URL, EXPLORER, GITHUB } from "@/lib/config";
import {
  attachSource,
  getOwner,
  getQuestion,
  getStats,
  listIds,
  openQuestion,
  settle,
  type QuestionRow,
} from "@/lib/contracts";
import { useWallet } from "./WalletProvider";

export function DualSourceApp() {
  const { address, provider, connect } = useWallet();
  const [rows, setRows] = useState<QuestionRow[]>([]);
  const [owner, setOwner] = useState("");
  const [stats, setStats] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const [tx, setTx] = useState("");

  const [qid, setQid] = useState("q1");
  const [question, setQuestion] = useState("Does the page contain Hello world?");
  const [url, setUrl] = useState(DEMO_URL);


  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [ids, o, s] = await Promise.all([listIds(), getOwner(), getStats()]);
      setOwner(o);
      setStats(JSON.stringify(s));
      const loaded = await Promise.all(ids.map((id) => getQuestion(id)));
      setRows(loaded.filter(Boolean) as QuestionRow[]);
      setMsg("");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "read failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const run = async (label: string, fn: () => Promise<string>) => {
    if (!address || !provider) {
      setMsg("Connect MetaMask for writes");
      return;
    }
    setBusy(label);
    try {
      const hash = await fn();
      setTx(hash);
      setMsg(`${label} OK`);
      await refresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy("");
    }
  };

  return (
    <main className="wrap">
      <header>
        <h1>DualSource Desk</h1>
        <p className="muted">
          Dual-URL fact resolution — freeze two sources, LLM consensus on{" "}
          <code>favor</code> (a|b|tie). Reads without wallet.
        </p>
        <div className="row">
          {address ? (
            <span className="pill ok">
              {address.slice(0, 6)}…{address.slice(-4)}
            </span>
          ) : (
            <button type="button" onClick={() => void connect()}>
              Connect MetaMask
            </button>
          )}
          <button type="button" onClick={() => void refresh()} disabled={loading}>
            {loading ? "Loading…" : "Refresh"}
          </button>
          <a href={EXPLORER} target="_blank" rel="noreferrer">
            Explorer
          </a>
          <a href={GITHUB} target="_blank" rel="noreferrer">
            GitHub
          </a>
        </div>
        {msg && <p className={msg.includes("OK") ? "ok" : "err"}>{msg}</p>}
        {tx && (
          <p className="muted">
            tx <code>{tx}</code>
          </p>
        )}
      </header>

      <section className="card">
        <h2>Questions</h2>
        <p className="muted">owner {owner || "—"} · {stats}</p>
        <ul>
          {rows.map((r) => (
            <li key={r.question_id}>
              <strong>{r.question_id}</strong> · {r.status}
              {r.favor ? ` · favor=${r.favor}` : ""} · sources{" "}
              {r.sources?.length ?? 0}
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>Asker flow</h2>
        <label>
          question_id
          <input value={qid} onChange={(e) => setQid(e.target.value)} />
        </label>
        <label>
          question
          <input value={question} onChange={(e) => setQuestion(e.target.value)} />
        </label>
        <label>
          source url
          <input value={url} onChange={(e) => setUrl(e.target.value)} />
        </label>
        <div className="row">
          <button
            type="button"
            disabled={!!busy}
            onClick={() =>
              void run("open", () =>
                openQuestion(address as `0x${string}`, provider, qid, question),
              )
            }
          >
            open_question
          </button>
          <button
            type="button"
            disabled={!!busy}
            onClick={() =>
              void run("attach", () =>
                attachSource(address as `0x${string}`, provider, qid, url),
              )
            }
          >
            attach_source
          </button>
          <button
            type="button"
            disabled={!!busy}
            onClick={() =>
              void run("settle", () =>
                settle(address as `0x${string}`, provider, qid),
              )
            }
          >
            settle
          </button>
        </div>
        <p className="muted">Call attach_source twice (A then B), then settle.</p>
      </section>
    </main>
  );
}
