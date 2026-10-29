import os
import time
import hashlib
import json
import requests
from fastapi import FastAPI, Query

app = FastAPI()

# Credenciais Shopee
SHOPEE_APP_KEY = os.getenv("SHOPEE_APP_KEY", "").strip()
SHOPEE_APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "").strip()

# Credenciais Mercado Livre
MELI_APP_ID = os.getenv("MELI_APP_ID", "").strip()
MELI_CLIENT_SECRET = os.getenv("MELI_CLIENT_SECRET", "").strip()

def generate_shopee_signature(payload_str, timestamp):
    base_string = f"{SHOPEE_APP_KEY}{timestamp}{payload_str}{SHOPEE_APP_SECRET}"
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

@app.get("/")
def home():
    return {"status": "API Shopee e Mercado Livre operacionais!"}

@app.get("/shopee-offers")
def get_shopee_offers(
    page: int = Query(1, description="Número da página"),
    limit: int = Query(100, description="Quantidade de produtos por busca (máx 100)")
):
    if not SHOPEE_APP_KEY or not SHOPEE_APP_SECRET:
        return {"error": "Chaves da Shopee nao configuradas!"}
        
    timestamp = int(time.time())
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    query_str = f"query{{productOfferV2(page:{page},limit:{limit},sortType:1){{nodes{{itemId,productName,imageUrl,price,offerLink}}}}}}"
    payload = {"query": query_str}
    payload_json_compact = json.dumps(payload, separators=(',', ':'))
    
    signature = generate_shopee_signature(payload_json_compact, timestamp)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={SHOPEE_APP_KEY}, Timestamp={timestamp}, Signature={signature}"
    }
    
    response = requests.post(url, data=payload_json_compact, headers=headers)
    return response.json()

@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ferramentas", description="Termo da busca"),
    limit: int = Query(20, description="Quantidade de produtos")
):
    """
    Busca produtos do catalogo oficial do Mercado Livre (MLB).
    Usa o endpoint /products/search que nao e bloqueado em servidores cloud.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    search_term = q.strip() if q and q.strip() else "ferramentas"
    url = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLB&q={search_term}&limit={limit}"
    
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        results = []
        
        if resp.status_code == 200:
            data = resp.json()
            raw_results = data.get("results", [])
            
            for item in raw_results:
                # Extrai foto do produto
                pictures = item.get("pictures", [])
                thumbnail = pictures[0].get("url") if pictures else ""
                
                # Extrai o menor preco ou preco medio do catalogo
                buy_box = item.get("buy_box_winner", {})
                price = buy_box.get("price") or item.get("price") or 0
                
                title = item.get("name") or item.get("title") or "Oferta Mercado Livre"
                item_id = item.get("id")
                
                results.append({
                    "id": item_id,
                    "title": title,
                    "permalink": f"https://www.mercadolivre.com.br/p/{item_id}",
                    "price": price,
                    "thumbnail": thumbnail,
                    "description": f"Aproveite esta oferta no Mercado Livre: {title}!"
                })
                
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}
