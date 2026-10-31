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

# Credenciais Mercado Livre & Scraper
MELI_APP_ID = os.getenv("MELI_APP_ID", "").strip()
MELI_CLIENT_SECRET = os.getenv("MELI_CLIENT_SECRET", "").strip()
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
    category: str = Query("todas", description="Termo de busca ou categoria"),
    limit: int = Query(8, description="Quantidade de produtos a retornar")
):
    # Trata a palavra "todas" para buscar termos com alto volume
    search_term = category.lower().strip()
    if search_term in ["todas", "mix", "all", ""]:
        search_terms = ["ofertas", "promocao", "tecnologia", "ferramentas", "casa"]
        search_term = random.choice(search_terms)

    target_url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit=50"
    
    # Se a SCRAPER_API_KEY estiver configurada, passa pela ScraperAPI para contornar bloqueios do Render
    if SCRAPER_API_KEY:
        search_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"
    else:
        search_url = target_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(search_url, headers=headers, timeout=15)
        data = resp.json()
        raw_results = data.get("results", [])
    except Exception as e:
        return {"error": f"Falha ao consultar Mercado Livre: {str(e)}"}

    if not raw_results:
        return {"results": [], "total": 0}

    # Embaralha os produtos para mudar a cada execução
    random.shuffle(raw_results)

    results = []
    for item in raw_results[:limit]:
        price = item.get("price", 0.0)
        original_price = item.get("original_price") or (price * 1.25)
        
        discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 20
        
        # Ajusta a imagem para HTTPS e alta resolução (compatível com Pinterest)
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
