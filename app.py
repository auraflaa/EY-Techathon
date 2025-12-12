# main.py
import os
import csv
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock MCP Server - Demo", version="1.0")

# ---------- Utility: load sample CSVs if present ----------
BASE_DIR = os.path.dirname(__file__)

def load_csv_to_list(path: str) -> List[Dict[str, str]]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)
    return rows

PRODUCTS_CSV = os.path.join(BASE_DIR, "products.csv")
INVENTORY_CSV = os.path.join(BASE_DIR, "inventory.csv")
CUSTOMERS_CSV = os.path.join(BASE_DIR, "customers.csv")
POLICY_DOC = os.path.join(BASE_DIR, "returns_policy.txt")

PRODUCTS = load_csv_to_list(PRODUCTS_CSV) or [
    {"sku":"SH123", "title":"Cotton Shirt", "desc":"Casual cotton shirt", "price":"1799", "sizes":"S|M|L", "image":""},
    {"sku":"DR234", "title":"Party Dress", "desc":"Floral party dress", "price":"2599", "sizes":"S|M|L", "image":""},
    {"sku":"SNK010","title":"Sneakers","desc":"Comfort sneakers","price":"2499","sizes":"8|9|10","image":""},
    {"sku":"TSH001","title":"Graphic Tee","desc":"Printed tee","price":"799","sizes":"M|L|XL","image":""},
    {"sku":"JKT09","title":"Light Jacket","desc":"Windproof jacket","price":"3499","sizes":"M|L|XL","image":""}
]

INVENTORY = load_csv_to_list(INVENTORY_CSV) or [
    {"sku":"SH123","store":"Indiranagar","size":"M","qty":"1"},
    {"sku":"SH123","store":"MallX","size":"M","qty":"0"},
    {"sku":"DR234","store":"Indiranagar","size":"M","qty":"2"},
    {"sku":"SNK010","store":"Online","size":"9","qty":"5"},
]

CUSTOMERS = load_csv_to_list(CUSTOMERS_CSV) or [
    {"user_id":"U100","size_profile":"M","loyalty_tier":"Silver"},
    {"user_id":"U101","size_profile":"9","loyalty_tier":"Gold"},
]

RETURNS_POLICY = ""
if os.path.exists(POLICY_DOC):
    with open(POLICY_DOC, "r", encoding="utf-8") as fh:
        RETURNS_POLICY = fh.read()
else:
    RETURNS_POLICY = (
        "Return policy: Items can be returned within 15 days of delivery if unused and tags intact. "
        "Return shipping is free for orders above ₹2000; otherwise standard charges apply. "
        "Certain categories (innerwear, final sale) are non-returnable. See in-app orders page for steps."
    )

# ---------- Request/Response models ----------
class RecommendReq(BaseModel):
    filters: Optional[Dict[str, Any]] = None
    user_profile: Optional[Dict[str, Any]] = None

class InventoryCheckReq(BaseModel):
    sku: str
    size: Optional[str] = None
    preferred_store: Optional[str] = None

class OffersReq(BaseModel):
    user_id: Optional[str] = None
    cart: List[Dict[str, Any]] = []
    coupon: Optional[str] = None

class PaymentReq(BaseModel):
    order_id: str
    amount: float
    method: str
    payment_metadata: Optional[Dict[str, Any]] = None

class FulfillmentReq(BaseModel):
    sku: str
    store: str
    slot: Optional[str] = None
    user_contact: Optional[str] = None

class SupportReq(BaseModel):
    order_id: Optional[str] = None
    question: Optional[str] = None
    issue: Optional[str] = None

# ---------- Endpoints ----------
@app.get("/health")
def health():
    return {"status":"ok", "time": datetime.utcnow().isoformat()}

@app.post("/recommend")
def recommend(req: RecommendReq):
    # Simple filter-based mock recommendation
    filters = req.filters or {}
    budget = filters.get("budget_max")
    category = filters.get("category", "").lower() if filters.get("category") else None
    size = filters.get("size")
    candidates = []
    for p in PRODUCTS:
        price = int(p.get("price", "0"))
        title = p.get("title","").lower()
        sku_sizes = p.get("sizes","").split("|")
        if budget and price > int(budget):
            continue
        if category and category not in title and category not in p.get("desc","").lower():
            # still include if category absent
            pass
        if size and size not in sku_sizes:
            # skip if size explicitly required and not available
            continue
        candidates.append({
            "sku": p["sku"],
            "title": p["title"],
            "price": price,
            "sizes": sku_sizes,
            "score": round(0.9 - (len(candidates)*0.05), 2)
        })
    # fallback: if no candidates, return top products
    if not candidates:
        candidates = [{
            "sku": p["sku"],
            "title": p["title"],
            "price": int(p["price"]),
            "sizes": p["sizes"].split("|"),
            "score": 0.5
        } for p in PRODUCTS[:3]]
    return {"candidates": candidates, "source":"mock_recommender"}

@app.post("/inventory/check")
def inventory_check(req: InventoryCheckReq):
    # compute online stock and per-store stock
    online_stock = 0
    store_stock = {}
    for row in INVENTORY:
        if row["sku"] != req.sku:
            continue
        qty = int(row.get("qty","0"))
        if row.get("store","").lower() == "online":
            online_stock += qty
        else:
            store_stock.setdefault(row["store"], 0)
            store_stock[row["store"]] += qty
    # if preferred_store provided, include it even if 0
    if req.preferred_store and req.preferred_store not in store_stock:
        store_stock[req.preferred_store] = 0
    # determine fulfillment options
    options = []
    if online_stock > 0:
        options.append("ship_to_home")
    if any(v>0 for v in store_stock.values()):
        options.append("click_and_collect")
    return {"online_stock": online_stock, "store_stock": store_stock, "fulfillment_options": options}

@app.post("/offers/apply")
def offers_apply(req: OffersReq):
    # simple loyalty discounts mock
    base_total = 0
    for it in (req.cart or []):
        sku = it.get("sku")
        qty = int(it.get("qty",1))
        prod = next((p for p in PRODUCTS if p["sku"]==sku), None)
        price = int(prod["price"]) if prod else 0
        base_total += price * qty
    discount = 0
    discounts = []
    if req.user_id:
        # mock loyalty tiers
        cust = next((c for c in CUSTOMERS if c["user_id"]==req.user_id), None)
        if cust and cust.get("loyalty_tier") == "Gold":
            discount = int(base_total * 0.05)
            discounts.append({"type":"loyalty_gold", "amount": discount})
    if req.coupon == "WELCOME50":
        discounts.append({"type":"coupon", "amount": 50})
        discount += 50
    final_price = max(0, base_total - discount)
    points = int(final_price / 100)
    return {"final_price": final_price, "discounts": discounts, "points_earned": points, "base_total": base_total}

@app.post("/payment/process")
def payment_process(req: PaymentReq):
    # deterministic success/failure behavior for demo
    # decline if amount > 5000 to simulate declines
    if req.amount > 5000:
        return {"status":"declined", "reason":"insufficient_funds"}
    tx = f"TXN-{uuid.uuid4().hex[:10].upper()}"
    return {"status":"approved", "tx_id": tx, "message":"success"}

@app.post("/fulfillment/reserve")
def fulfillment_reserve(req: FulfillmentReq):
    # simple reservation logic: if store has stock >0, reserve and return code, else 409
    # find inventory for sku and store
    found = None
    for r in INVENTORY:
        if r["sku"]==req.sku and r["store"].lower()==req.store.lower():
            if int(r.get("qty",0)) > 0:
                found = r
                break
    if not found:
        # return 409 with alternative slots suggestion
        alt_slots = [
            (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            (datetime.utcnow() + timedelta(hours=48)).isoformat()
        ]
        raise HTTPException(status_code=409, detail={"status":"slot_unavailable", "alternatives": alt_slots})
    # decrement mock stock (in-memory)
    found["qty"] = str(max(0, int(found.get("qty","0")) - 1))
    code = str(uuid.uuid4().hex[:6]).upper()
    eta = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    return {"status":"reserved", "pickup_code": code, "eta": eta}

@app.post("/support/query")
def support_query(req: SupportReq):
    # If question contains "return", return policy excerpt
    q = (req.question or req.issue or "").lower()
    if "return" in q or "refund" in q:
        return {"answer": RETURNS_POLICY, "source_doc": "returns_policy.txt"}
    if "track" in q or "where" in q:
        return {"answer": "To track your order, go to Orders -> Select order -> Track. Estimated delivery shown there.", "source_doc":"tracking_faq"}
    # default fallback
    return {"answer": "Please provide your order id so we can look up delivery status or returns instructions.", "source_doc":"faq_default"}
