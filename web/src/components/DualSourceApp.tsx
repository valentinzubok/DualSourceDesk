"use client";

import { useCallback, useEffect, useState } from "react";
import { CHAIN_ID, DEMO_URL, EXPLORER, GITHUB, txUrl } from "@/lib/config";
import { fundWithTestGen, getNativeBalance } from "@/lib/genlayer";
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
  const { address, provider, connect, error: walletError } = useWallet();
  const [rows, setRows] = useState<QuestionRow[]>([]);
  const [owner, setOwner] = useState("");
  const [stats, setStats] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const [tx, setTx] = useState("");
  const [gen, setGen] = useState("");

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
      setRows((loaded.filter(Boolean) as QuestionRow[]).reverse());
      if (address) setGen(await getNativeBalance(address));
    } catch (e) {
      setMsg(`Error: ${e instanceof Error ? e.message : "read failed"}`);
    } finally {
      setLoading(false);
    }
  }, [address]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const run = async (label: string, fn: () => Promise<string | void>) => {
    if (!address || !provider) {
      setMsg("Connect MetaMask for writes");
      return;
    }
    setBusy(label);
    setMsg("");
    try {
      const hash = await fn();
      if (hash) setTx(hash);
      await refresh();
      setMsg(`${label} OK`);
    } catch (e) {
      setMsg(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBusy("");
    }
  };

  return (
    <main className="wrap">
      <header>
        <h1>DualSource Desk</h1>
        <p className="muted">
          Dual-URL fact resolution on GenLayer Studio Dev (chain {CHAIN_ID}): validators freeze two
          sources (SHA-256), then settle <code>favor</code> (a|b|tie). Identical hashes give a
          deterministic tie; otherwise validators&apos; LLMs agree on the verdict. Every value below
          is read from the contract; reads work without a wallet.
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
          {address && (
            <button
              type="button"
              disabled={!!busy}
              onClick={() => void run("faucet", () => fundWithTestGen(address as `0x${string}`))}
            >
              Get test GEN{gen ? ` (${gen})` : ""}
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
        {(msg || walletError) && (
          <p className={msg.endsWith("OK") ? "ok" : "err"}>{msg || walletError}</p>
        )}
        {busy && <p className="muted">Waiting for GenLayer consensus: {busy}…</p>}
        {tx && (
          <p className="muted">
            last tx{" "}
            <a href={txUrl(tx)} target="_blank" rel="noreferrer">
              <code>{tx}</code>
            </a>
          </p>
        )}
      </header>

      <section className="card">
        <h2>Questions</h2>
        <p className="muted">owner {owner || "—"} · {stats}</p>
        <ul>
          {rows.length === 0 && <li className="muted">No questions yet</li>}
          {rows.map((r) => (
            <li key={r.question_id}>
              <strong>{r.question_id}</strong> · {r.status}
              {r.favor ? ` · favor=${r.favor}` : ""} · {r.question}
              {(r.sources ?? []).map((src) => (
                <div key={src.label} className="muted">
                  {src.label}: <code>sha256 {src.content_hash.slice(0, 16)}…</code> {src.url}
                </div>
              ))}
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
            disabled={!!busy || !address}
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
            disabled={!!busy || !address}
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
            disabled={!!busy || !address}
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
