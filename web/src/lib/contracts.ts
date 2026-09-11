import { CONTRACT_ADDRESS } from "./config";
import { type Address, parseJson, readContract, writeAndWait } from "./genlayer";

export type QuestionRow = {
  question_id: string;
  asker: string;
  question: string;
  status: string;
  favor?: string;
  sources?: { label: string; url: string; content_hash: string }[];
};

export async function listIds(): Promise<string[]> {
  const raw = await readContract<string>(CONTRACT_ADDRESS, "list_ids", []);
  return parseJson<string[]>(raw, []);
}

export async function getQuestion(id: string): Promise<QuestionRow | null> {
  const raw = await readContract<string>(CONTRACT_ADDRESS, "get_question", [id]);
  const parsed = parseJson<QuestionRow & { error?: string }>(raw, {} as QuestionRow);
  if ("error" in parsed && parsed.error) return null;
  return parsed.question_id ? parsed : null;
}

export async function getOwner(): Promise<string> {
  return (await readContract<string>(CONTRACT_ADDRESS, "get_owner", [])) || "";
}

export async function getStats() {
  const raw = await readContract<string>(CONTRACT_ADDRESS, "get_stats", []);
  return parseJson(raw, null);
}

export async function openQuestion(
  account: Address,
  provider: unknown,
  id: string,
  question: string,
) {
  return writeAndWait(account, provider, CONTRACT_ADDRESS, "open_question", [
    id,
    question,
  ]);
}

export async function attachSource(
  account: Address,
  provider: unknown,
  id: string,
  url: string,
) {
  return writeAndWait(account, provider, CONTRACT_ADDRESS, "attach_source", [id, url]);
}

export async function settle(account: Address, provider: unknown, id: string) {
  return writeAndWait(account, provider, CONTRACT_ADDRESS, "settle", [id]);
}
