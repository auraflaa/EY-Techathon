# Mock MCP Server — Agentic Retail System (FastAPI)

A lightweight **Mock MCP Server** designed for use in Agentic AI prototypes (e.g., EY Techathon 6.0).  
This backend provides deterministic, easy-to-demo endpoints for:

- Product Recommendations  
- Inventory Availability  
- Loyalty & Offers  
- Payment Simulation  
- Fulfillment (Reserve in Store)  
- Post-Purchase Support (RAG-like responses)  

The server is compatible with:

- **LangSmith**  
- **LangChain / LangGraph**  
- **LLM-based Orchestrator Agents**  
- **Sales Agent → MCP → Worker Agents** architecture  

You can deploy this entire server to **Render** in under 1 minute.

---

## 📦 Features

This Mock MCP server provides the following endpoints:

| Endpoint | Description |
|----------|-------------|
| `POST /recommend` | Returns mock product recommendations based on filters |
| `POST /inventory/check` | Checks online + store inventory for a SKU |
| `POST /offers/apply` | Applies mock loyalty discounts & coupons |
| `POST /payment/process` | Simulates payment success/failure |
| `POST /fulfillment/reserve` | Reserves items for in-store pickup |
| `POST /support/query` | Mock RAG responses for returns, tracking, FAQs |
| `GET /health` | Health check |

---

## 🔧 Local Setup

### 1. Clone the repository
```bash
git clone <your_repo_url>
cd mock-mcp-server
```

### 2. Create virtual environment & install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the server
```bash
uvicorn main:app --reload --port 8100
```

### 4. Test endpoints

Recommendation:
```bash
curl -X POST "http://localhost:8100/recommend" -H "Content-Type: application/json" -d '{"filters":{"budget_max":2000,"category":"shirts","size":"M"}}'
```

Inventory:
```bash
curl -X POST "http://localhost:8100/inventory/check" -H "Content-Type: application/json" -d '{"sku":"SH123","size":"M","preferred_store":"Indiranagar"}'
```

---

## 🚀 Deploying to Render (Free Tier)

### 1. Push repo to GitHub  
Ensure the repo contains: `main.py`, `requirements.txt`, `Procfile`, `README.md`.

### 2. On Render.com
- New → Web Service  
- Connect GitHub repo  
- Set:

| Setting | Value |
|--------|--------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn -k uvicorn.workers.UvicornWorker main:app --log-file -` |
| Environment | Python 3.x |

### 3. After deploy
Your public MCP URL will look like:

```
https://your-mcp-service.onrender.com
```

Use this in LangSmith or your Sales Agent.

---

## 📁 Optional CSV Data

`products.csv`:
```
sku,title,desc,price,sizes,image
SH123,Cotton Shirt,Casual cotton shirt,1799,S|M|L,
DR234,Party Dress,Floral party dress,2599,S|M|L,
SNK010,Sneakers,Comfort sneakers,2499,8|9|10,
TSH001,Graphic Tee,Printed tee,799,M|L|XL,
JKT09,Light Jacket,Windproof jacket,3499,M|L|XL,
```

`inventory.csv`:
```
sku,store,size,qty
SH123,Indiranagar,M,1
SH123,MallX,M,0
DR234,Indiranagar,M,2
SNK010,Online,9,5
TSH001,Online,M,10
```

`customers.csv`:
```
user_id,size_profile,loyalty_tier
U100,M,Silver
U101,9,Gold
```

`returns_policy.txt` — any text describing return rules.

---

## 🧠 Architecture (Where MCP fits)

```
User → Sales Agent (LLM) → MCP Server → Worker Endpoints → MCP → Sales Agent → User
```

Sales Agent outputs JSON actions like:

```json
{"action": "recommend", "params": {...}}
```

MCP routes to `/recommend`, returns results, and Sales Agent generates a natural reply.

---

## 🔐 Security Notes
- This is a mock server: **do not** use real PII or process real payments.  
- Add API key middleware for public deployment.  
- Mask user logs where needed.

---

## 📝 License
MIT License — free to use and modify.

