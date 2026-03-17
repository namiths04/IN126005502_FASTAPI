from fastapi import FastAPI, Query, HTTPException
from typing import Optional, List
import math

app = FastAPI(title="FastAPI Day 6 Assignment")

# --- DATA MODELS (Mock Data) ---
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics"},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery"},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics"},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery"},
]

orders = [] # This will be populated via POST /orders

# --- EXISTING ENDPOINTS (Q1, Q2, Q3) ---

@app.get("/products/search")
def search_products(keyword: str):
    results = [p for p in products if keyword.lower() in p['name'].lower()]
    if not results:
        return {"message": f"No products found for: {keyword}"}
    return {"keyword": keyword, "total_found": len(results), "products": results}

@app.get("/products/sort")
def sort_products(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name"]:
        raise HTTPException(status_code=400, detail="sort_by must be 'price' or 'name'")
    
    is_reverse = (order == "desc")
    sorted_data = sorted(products, key=lambda p: p[sort_by], reverse=is_reverse)
    return {"sort_by": sort_by, "order": order, "products": sorted_data}

@app.get("/products/page")
def paginate_products(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    total_pages = math.ceil(len(products) / limit)
    return {
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "products": products[start:end]
    }

# --- NEW ASSIGNMENT ENDPOINTS (Q4, Q5, Q6) ---

# Q4: Search Orders by Customer Name
@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    results = [
        o for o in orders 
        if customer_name.lower() in o['customer_name'].lower()
    ]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {"customer_name": customer_name, "total_found": len(results), "orders": results}

# Q5: Sort Products by Category (A-Z) then Price (Low-High)
@app.get("/products/sort-by-category")
def sort_by_category():
    # Sorts primarily by category, then by price if categories are the same
    result = sorted(products, key=lambda p: (p['category'], p['price']))
    return {"products": result, "total": len(result)}

# Q6: The "Master" Browse Endpoint (Search + Sort + Paginate)
@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20)
):
    # 1. Search/Filter
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p['name'].lower()]

    # 2. Sort
    if sort_by in ['price', 'name']:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == 'desc'))

    # 3. Paginate
    total = len(result)
    start = (page - 1) * limit
    paged_result = result[start : start + limit]

    return {
        "filters": {"keyword": keyword, "sort_by": sort_by, "order": order},
        "pagination": {
            "page": page, 
            "limit": limit, 
            "total_found": total, 
            "total_pages": math.ceil(total / limit)
        },
        "products": paged_result
    }

# Bonus: Paginate Orders
@app.get("/orders/page")
def get_orders_paged(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    start = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "total_orders": len(orders),
        "total_pages": math.ceil(len(orders) / limit),
        "orders": orders[start : start + limit]
    }

# Helper to add orders for testing Q4 and Bonus
@app.post("/orders")
def create_order(customer_name: str, item: str):
    new_id = len(orders) + 1
    order = {"order_id": new_id, "customer_name": customer_name, "item": item}
    orders.append(order)
    return order