import os
import time
import hashlib
import json
import requests
from fastapi import FastAPI, Query

app = FastAPI()

APP_KEY = os.getenv("SHOPEE_APP_KEY", "").strip()
APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "").strip()

def generate_signature(payload_str, timestamp):
    base_string = f"{APP_KEY}{timestamp}{payload_str}{APP_SECRET}"
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

@app.get("/")
def home():
    return {"status": "API Shopee e Mercado Livre a rodar de forma segura!"}

@app.get("/shopee-offers")
def get_shopee_offers(
    page: int = Query(1, description="Número da página"),
    limit: int = Query(100, description="Quantidade de produtos por busca (máx 100)")
):
    if not APP_KEY or not APP_SECRET:
        return {"error": "Chaves da Shopee nao configuradas nas Variaveis de Ambiente!"}
        
    timestamp = int(time.time())
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    query_str = f"query{{productOfferV2(page:{page},limit:{limit},sortType:1){{nodes{{itemId,productName,imageUrl,price,offerLink}}}}}}"
    payload = {"query": query_str}
    payload_json_compact = json.dumps(payload, separators=(',', ':'))
    
    signature = generate_signature(payload_json_compact, timestamp)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_KEY}, Timestamp={timestamp}, Signature={signature}"
    }
    
    response = requests.post(url, data=payload_json_compact, headers=headers)
    return response.json()

@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("casa", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    search_term = q.strip() if q and q.strip() else "casa"
    
    # URL da API de busca do Mercado Livre
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # Se a busca por palavra falhar, usa a categoria geral de ofertas (MLB1051)
        if response.status_code != 200 or not response.json().get("results"):
            fallback_url = f"https://api.mercadolibre.com/sites/MLB/search?category=MLB1051&limit={limit}"
            response = requests.get(fallback_url, headers=headers, timeout=15)
            
        data = response.json()
        raw_results = data.get("results", [])
        
        results = []
        for item in raw_results:
            results.append({
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "permalink": item.get("permalink", ""),
                "price": item.get("price", 0),
                "thumbnail": item.get("thumbnail", ""),
                "description": f"Oferta especial: {item.get('title', '')} por R$ {item.get('price', 0)}"
            })
            
        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}
