# DualSource — Studio Dev (chain 61997) deploy record

| | |
|---|---|
| **Network** | GenLayer Studio Dev / Studio Next — chain `61997`, GenVM `v0.3.0-rc7` |
| **Contract** | [`0xF4402034209D51F683ae5BC61ddd6b1AdC610ED3`](https://explorer-studio-dev.genlayer.com/address/0xF4402034209D51F683ae5BC61ddd6b1AdC610ED3) |
| **Owner** | `0x6f6077eC587f2964d30aCE8D803Edc27988046e3` |
| **Source** | [`contracts/DualSource.py`](contracts/DualSource.py) — runner `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng` |
| **Source sha256** | `325e8aa72907c0863e2203c6db26215530162f2ac08d77a12b438adf397c17b9` |

## Verify

```bash
curl -s -X POST https://studio-dev.genlayer.com/api -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"gen_getContractCode","params":["0xF4402034209D51F683ae5BC61ddd6b1AdC610ED3"]}' \
  | python3 -c "import sys,json,base64,hashlib; print(hashlib.sha256(base64.b64decode(json.load(sys.stdin)['result'])).hexdigest())"
shasum -a 256 contracts/DualSource.py
```

## On-chain lifecycle (all `ACCEPTED`, execution `SUCCESS`)

| # | Step | Result | Tx |
|---|------|--------|----|
| 0 | deploy | contract created | `0x081cb3d158ce4d4c4789586db960b7d914756365337dee7d3d482ae1bd5e8956` |
| 1 | `open_question("q1", "Does the page say Hello world?")` | open | `0xcfe08cbdbc85a491a193751c2ddf5c0e31cc0c2b7139cb3998128191995652d8` |
| 2 | `attach_source("q1", hello.html)` | source a frozen, sha256 `c0535e4b…` | `0x39a68f74b0527419ed0ca71ee70cded92fc35d9b8f3170aa8356bc5417eb9888` |
| 3 | `attach_source("q1", hello.html)` | source b frozen, same hash | `0x9c7523fc5bfd66f29f7666f87182b58a2884c932ece981639d24fae2938f9653` |
| 4 | `settle("q1")` | **favor = tie** (identical hashes, deterministic) | `0x8a8591758e080a7ea502c6633c12c90b2e20d8901b8d1bd8eb8e60049bf42edf` |
| 5 | `open_question("q2", "Which source says Hello world?")` | open | `0xbeede5fa36944990e5435d3a280e51a5b4086609dac16bc531574841c109a89c` |
| 6 | `attach_source("q2", hello.html)` | source a frozen | `0x172f82c4e729b598ddb269dd05af2da486e5e83f1a4afc1f6856367179468785` |
| 7 | `attach_source("q2", https://example.com/)` | source b frozen, sha256 `8c1e8564…` | `0x0ad04988a7aa32650023af8b8badb0990eae98cd07d5b52f75cf818a437d6449` |
| 8 | `settle("q2")` | validators' LLMs on frozen previews give **favor = a** | `0xaa69776332a86058843a6407e08566496020fe5f19920d02de53e98843a8ae9a` |

State (`get_stats`): `{"total": 2, "by_status": {"resolved": 2}}`

## Demo video

[`assets/demo/dualsource-desk-demo.mp4`](https://github.com/valentinzubok/DualSourceDesk/blob/main/assets/demo/dualsource-desk-demo.mp4): 2:14 recording of the live app, with no mocks. It shows:
- chain state loaded without a wallet → connect
- `open_question("q-demo")` → `attach_source` hello.html → `attach_source` example.com → `settle`
- the result: **favor = b**, and the tx on the explorer

For an unattended recording, a small EIP-1193 wallet signing with test keys is injected in place of the MetaMask popup. Consensus waits are sped up 8x and rate-limit pauses are cut.
