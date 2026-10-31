import os
import time
import hashlib
import json
import random
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
    category: str = Query("todas", description="Termo de busca ou categoria"),
    limit: int = Query(8, description="Quantidade de produtos a retornar")
):
    search_term = category.lower().strip()
    if search_term in ["todas", "mix", "all", ""]:
        search_terms = ["tecnologia", "ferramentas", "casa", "smartphones", "utilidades", "audio", "games"]
        search_term = random.choice(search_terms)

    # Consulta direta à API do Mercado Livre Brasil com filtros de busca dinâmica
    search_url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&sort=relevance"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    raw_results = []
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            raw_results = data.get("results", [])
    except Exception:
        raw_results = []

    # Caso a busca retorne vazia, tenta uma rota secundária de itens em alta
    if not raw_results:
        try:
            fallback_url = "https://api.mercadolibre.com/sites/MLB/search?q=promocao"
            resp = requests.get(fallback_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                raw_results = resp.json().get("results", [])
        except Exception:
            raw_results = []

    random.shuffle(raw_results)

    results = []
    for item in raw_results[:limit]:
        price = item.get("price", 0.0)
        original_price = item.get("original_price") or (price * 1.22)
        
        discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 18
        
        # Ajusta a URL da imagem para HTTPS e alta definição
        thumbnail = item.get("thumbnail", "").replace("http://", "https://")
        if "-I.jpg" in thumbnail:
            thumbnail = thumbnail.replace("-I.jpg", "-O.jpg")
        elif "-I.webp" in thumbnail:
            thumbnail = thumbnail.replace("-I.webp", "-O.webp")

        permalink = item.get("permalink", "")

        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "permalink": permalink,
            "coupon_link": "https://www.mercadolivre.com.br/cupons",
            "original_price": round(original_price, 2),
            "price": round(price, 2),
            "discount": f"{discount_pct}%",
            "coupon": "OFERTAMELI",
            "thumbnail": thumbnail,
            "description": f"Aproveite esta super oferta: {item.get('title')}"
        })

    return {"results": results, "total": len(results)}
