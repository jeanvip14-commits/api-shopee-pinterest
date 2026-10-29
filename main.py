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
    ids: str = Query(None, description="IDs de anúncios separados por vírgula")
):
    # IDs reais e ativos de produtos populares no Mercado Livre Brasil (MLB)
    default_ids = ["MLB3202518100", "MLB2815147890", "MLB3300124580", "MLB2105128940"]
    
    if ids and ids.strip():
        item_ids_list = [i.strip() for i in ids.split(",") if i.strip()]
    else:
        item_ids_list = default_ids
        
    ids_param = ",".join(item_ids_list)
    url = f"https://api.mercadolibre.com/items?ids={ids_param}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        results = []
        
        if resp.status_code == 200:
            items_data = resp.json()
            for doc in items_data:
                # Processa itens válidos (status 200)
                if doc.get("code") == 200:
                    body = doc.get("body", {})
                    results.append({
                        "id": body.get("id"),
                        "title": body.get("title"),
                        "permalink": body.get("permalink"),
                        "price": body.get("price"),
                        "thumbnail": body.get("secure_thumbnail") or body.get("thumbnail"),
                        "description": f"Aproveite esta oferta no Mercado Livre: {body.get('title')} por R$ {body.get('price')}"
                    })
                    
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}
