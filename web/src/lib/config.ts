export const CONTRACT_ADDRESS = (process.env.NEXT_PUBLIC_DUALSOURCE_ADDRESS ??
  "0xF53cf71b99d17a37f00238f0d71F3C60d88A2079") as `0x${string}`;

export const EXPLORER = `https://explorer-studio.genlayer.com/address/${CONTRACT_ADDRESS}`;

export const GITHUB = "https://github.com/valentinzubok/DualSourceDesk";

export const DEMO_URL = "https://test-server.genlayer.com/static/genvm/hello.html";
