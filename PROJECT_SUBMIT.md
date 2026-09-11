# DualSourceDesk — Projects submission

**Type:** Builder → **Projects**

## Pairing

- **DualSource** = IC-only repo → Intelligent Contracts
- **DualSourceDesk** = this console → Projects

## After Studio deploy

1. `NEXT_PUBLIC_DUALSOURCE_ADDRESS=0x…`
2. Update `web/src/lib/config.ts`
3. Vercel deploy `web/`
4. Screenshot → `docs/console-screenshot.png`

## Title
```text
DualSource Desk — dual-URL fact console (Next.js + favor consensus)
```

## Notes
```text
DualSource Desk is a GenLayer Project: Next.js console for dual-source fact resolution.

Use case: open_question → attach_source ×2 (freeze SHA-256) → resolve with LLM consensus on {"favor":"a"|"b"|"tie"} from frozen previews only.

Intelligent Contract (in-repo): contracts/DualSource.py
Live app: REPLACE_VERCEL_URL
Studionet: 0xF53cf71b99d17a37f00238f0d71F3C60d88A2079
GitHub: https://github.com/valentinzubok/DualSourceDesk

Reads without wallet. Writes need MetaMask.
```

## Evidence
1. GitHub
2. Vercel
3. Explorer address
4. Screenshot
5. DualSource.py blob
