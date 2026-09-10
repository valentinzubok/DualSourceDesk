export const CONTRACT_ADDRESS = (process.env.NEXT_PUBLIC_DUALSOURCE_ADDRESS ??
  "0x0000000000000000000000000000000000000000") as `0x${string}`;

export const EXPLORER = `https://explorer-studio.genlayer.com/address/${CONTRACT_ADDRESS}`;

export const GITHUB = "https://github.com/valentinzubok/DualSourceDesk";

export const DEMO_URL = "https://test-server.genlayer.com/static/genvm/hello.html";
