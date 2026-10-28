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

def get_meli_access_token():
    """Gera token via Client Credentials caso as chaves estejam presentes"""
    if not MELI_APP_ID or not MELI_CLIENT_SECRET:
        return None
        
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": MELI_APP_ID,
        "client_secret": MELI_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get("access_token")
    except Exception:
        pass
    return None

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
    q: str = Query("ferramentas", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    token = get_meli_access_token()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    search_term = q.strip() if q and q.strip() else "ferramentas"
    
    # 1. Tenta buscar pelo termo especificado
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    try:
        response = requests.get(url, headers=headers, timeout=12)
        data = response.json()
        raw_results = data.get("results", [])
        
        # 2. Se a busca por termo vier vazia, consulta por categoria de ofertas (MLB1051 - Ferramentas e Casa)
        if not raw_results:
            fallback_url = f"https://api.mercadolibre.com/sites/MLB/search?category=MLB1051&limit={limit}"
            response = requests.get(fallback_url, headers=headers, timeout=12)
            data = response.json()
            raw_results = data.get("results", [])
            
        results = []
        for item in raw_results:
            results.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "permalink": item.get("permalink"),
                "price": item.get("price"),
                "thumbnail": item.get("thumbnail"),
                "description": f"Aproveite esta oferta no Mercado Livre: {item.get('title')} por R$ {item.get('price')}"
            })
                
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}
