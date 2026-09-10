import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import type { CalldataEncodable } from "genlayer-js/types";
import { TransactionStatus } from "genlayer-js/types";

export type Address = `0x${string}`;

type EthereumProvider = NonNullable<Parameters<typeof createClient>[0]>["provider"];

export function getReadClient() {
  return createClient({ chain: studionet });
}

export function getWriteClient(account: Address, provider: EthereumProvider) {
  return createClient({ chain: studionet, account, provider });
}

export async function readContract<T = unknown>(
  address: Address,
  functionName: string,
  args: CalldataEncodable[] = [],
): Promise<T> {
  const client = getReadClient();
  return client.readContract({ address, functionName, args }) as Promise<T>;
}

export async function writeAndWait(
  account: Address,
  provider: unknown,
  address: Address,
  functionName: string,
  args: CalldataEncodable[] = [],
): Promise<string> {
  const client = getWriteClient(account, provider as EthereumProvider);
  await client.connect("studionet");
  const hash = await client.writeContract({
    address,
    functionName,
    args,
    value: BigInt(0),
  });
  await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
  });
  return hash;
}

export function parseJson<T>(raw: string, fallback: T): T {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}
