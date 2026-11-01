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

# Tag de Afiliado Mercado Livre (opcional)
MELI_AFFILIATE_TAG = os.getenv("MELI_AFFILIATE_TAG", "").strip()

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
    # Sorteia um nicho amplo de ofertas reais caso venha 'todas'
    search_term = category.lower().strip()
    if search_term in ["todas", "mix", "all", ""]:
        search_terms = ["tecnologia", "smartphones", "ferramentas", "fone bluetooth", "smartwatch", "casa", "gamer"]
        search_term = random.choice(search_terms)

    search_url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit=50"
    
    # User-Agent de navegador para evitar o bloqueio silencioso do Render
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    raw_items = []
    try:
        resp = requests.get(search_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            raw_items = data.get("results", [])
    except Exception:
        raw_items = []

    # Se a palavra sorteada não trouxer itens, faz um fallback direto para ofertas gerais ativas
    if not raw_items:
        try:
            fallback_url = "https://api.mercadolibre.com/sites/MLB/search?q=oferta&limit=50"
            resp_fb = requests.get(fallback_url, headers=headers, timeout=8)
            if resp_fb.status_code == 200:
                raw_items = resp_fb.json().get("results", [])
        except Exception:
            raw_items = []

    # Filtra produtos que tenham permalink oficial válido da API do Mercado Livre
    valid_products = [item for item in raw_items if item.get("permalink") and item.get("title")]

    if not valid_products:
        return {"results": [], "total": 0}

    # Embaralha o catálogo retornado para variar as ofertas no Make
    random.shuffle(valid_products)

    results = []
    for item in valid_products[:limit]:
        price = item.get("price", 0.0)
        original_price = item.get("original_price") or (price * 1.25)
        discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 15
        
        # PERMALINK OFICIAL DIRETO DO ANÚNCIO NO MERCADO LIVRE
        permalink = item.get("permalink", "")
        if MELI_AFFILIATE_TAG and permalink:
            separator = "&" if "?" in permalink else "?"
            permalink = f"{permalink}{separator}matt_tool={MELI_AFFILIATE_TAG}"

        # Ajusta imagem para alta definição
        thumbnail = item.get("thumbnail", "").replace("http://", "https://")
        if "-I.jpg" in thumbnail:
            thumbnail = thumbnail.replace("-I.jpg", "-O.jpg")
        elif "-I.webp" in thumbnail:
            thumbnail = thumbnail.replace("-I.webp", "-O.webp")

        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "permalink": permalink,  # LINK DIRETO E REAL DA PÁGINA DO ANÚNCIO
            "coupon_link": "https://www.mercadolivre.com.br/cupons",
            "original_price": round(original_price, 2),
            "price": round(price, 2),
            "discount": f"{discount_pct}%",
            "coupon": "OFERTAMELI",
            "thumbnail": thumbnail,
            "description": f"Aproveite esta oferta imperdível: {item.get('title')}"
        })

    return {"results": results, "total": len(results)}
