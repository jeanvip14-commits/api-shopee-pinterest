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
    ids: str = Query("MLB3202518100,MLB2815147890,MLB3300124580,MLB2105128940", description="IDs de anúncios separados por vírgula")
):
    """
    Busca detalhes diretos de anúncios ativos no Mercado Livre Brasil.
    Este endpoint (/items?ids=...) é 100% livre de bloqueios da Cloudflare.
    """
    # Lista de IDs padrão de produtos populares caso nenhum seja passado
    default_ids = ["MLB3202518100", "MLB2815147890", "MLB3300124580", "MLB2105128940"]
    
    if ids and ids.strip():
        raw_ids = [i.strip() for i in ids.split(",") if i.strip()]
    else:
        raw_ids = default_ids
        
    ids_param = ",".join(raw_ids[:20]) # Suporta até 20 anúncios por chamada
    url = f"https://api.mercadolibre.com/items?ids={ids_param}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        results = []
        
        if resp.status_code == 200:
            data = resp.json()
            for doc in data:
                if doc.get("code") == 200:
                    body = doc.get("body", {})
                    results.append({
                        "id": body.get("id"),
                        "title": body.get("title"),
                        "permalink": body.get("permalink"),
                        "price": body.get("price"),
                        "thumbnail": body.get("secure_thumbnail") or body.get("thumbnail"),
                        "description": f"Confira esta oferta no Mercado Livre: {body.get('title')} por R$ {body.get('price')}"
                    })
                    
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": [], "total": 0}
