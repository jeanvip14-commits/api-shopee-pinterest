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

# Chave ScraperAPI
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "").strip()

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
    limit: int = Query(50, description="Quantidade de produtos")
):
    search_term = q.strip() if q and q.strip() else "ferramentas"
    target_url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    if SCRAPER_API_KEY:
        # Envia através do ScraperAPI para contornar a Cloudflare
        url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"
    else:
        url = target_url

    headers = {"Accept": "application/json"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=25)
        results = []
        
        if resp.status_code == 200:
            data = resp.json()
            raw_results = data.get("results", [])
            
            for item in raw_results:
                results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "permalink": item.get("permalink"),
                    "price": item.get("price"),
                    "thumbnail": item.get("secure_thumbnail") or item.get("thumbnail"),
                    "description": f"Confira esta oferta no Mercado Livre: {item.get('title')} por R$ {item.get('price')}"
                })
                
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}
