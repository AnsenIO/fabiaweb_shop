# fabiaweb_shop

Pre-order storefront for **FABIABox** sovereign AI hardware and agentic services.

**Live target:** https://shop.fabiabox.com/

## What it does

- Lists 4 FABIABox hardware tiers + 2 agentic service plans.
- Lets visitors **pre-buy** (with reservation deposit) or join the **waiting list**.
- Stores order requests in `data/orders.csv`.
- Notifies via cron + Telegram sync, same pattern as `fabia_web`.

## Catalog

| SKU | Category | Price / Reservation |
|-----|----------|---------------------|
| FABIABox Entry | Hardware (AMD Ryzen AI Max+) | Price on request / €500 reservation |
| FABIABox Edge | Hardware (NVIDIA Thor) | Price on request / €500 reservation |
| FABIABox Pro | Hardware (NVIDIA DGX Spark, 1 PFlop) | Price on request / €500 reservation |
| FABIABox Enterprise | Hardware (NVIDIA DGX roadmap, 20 PFlop) | Price on request / €500 reservation |
| Agentic Build Plan | Service | €49.99/mo or €499/yr |
| Agentic Operate Plan | Service | €49.99/mo or €499/yr |

## Tech stack

- Static HTML + Tailwind CSS
- Flask `/submit` endpoint
- nginx reverse proxy on `shop.fabiabox.com`
- gunicorn on loopback `127.0.0.1:8081`
- `deploy.sh` + `fetch-orders.sh` (base64-over-SSH, like `fabia_web`)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Tests:

```bash
python test.py
```

## Deploy

```bash
./deploy.sh
```

Pull orders from droplet:

```bash
./fetch-orders.sh
```

## Starter material

| File | Source |
|------|--------|
| `README-fabia_web.md` | `fabia_web/README.md` |
| `CONTEXT-fabia_web.md` | `fabia_web/CONTEXT.md` |
| `README-fabia-0.3.md` | `fabia-0.3/README.md` |
| `AGENTS-fabia-0.3.md` | `fabia-0.3/AGENTS.md` |
| `CONTEXT-fabia-0.3.md` | `fabia-0.3/CONTEXT.md` |

## License

Private — IABAI Network
