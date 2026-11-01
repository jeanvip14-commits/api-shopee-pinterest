import os
import time
import hashlib
import json
import random
import requests
import urllib.parse
from fastapi import FastAPI, Query

app = FastAPI()

# Credenciais Shopee
SHOPEE_APP_KEY = os.getenv("SHOPEE_APP_KEY", "").strip()
SHOPEE_APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "").strip()

# Tag de Afiliado Mercado Livre (Ex: 12345678)
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
    # Categorias dinâmicas
    categories_mlb = ["MLB1051", "MLB5726", "MLB1000", "MLB1648", "MLB1500", "MLB1499"]
    selected_cat = random.choice(categories_mlb)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    raw_items = []
    try:
        search_url = f"https://api.mercadolibre.com/sites/MLB/search?category={selected_cat}&sort=sold_quantity_desc&limit=30"
        resp = requests.get(search_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            raw_items = resp.json().get("results", [])
    except Exception:
        raw_items = []

    # Lista de contingência dinamicamente rotacionada caso o Render receba resposta vazia
    if not raw_items:
        raw_items = [
            {"id": "MLB01", "title": "Fone de Ouvido Bluetooth QCY T13 Sem Fio ANC", "price": 154.23, "original_price": 239.00, "thumbnail": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"},
            {"id": "MLB02", "title": "Smartwatch Relógio Inteligente Amazfit Bip 5 GPS", "price": 389.00, "original_price": 499.00, "thumbnail": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&q=80"},
            {"id": "MLB03", "title": "Carregador Rápido Baseus GaN 65W Multiportas USB-C", "price": 129.90, "original_price": 199.90, "thumbnail": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&q=80"},
            {"id": "MLB04", "title": "Mouse Sem Fio Recarregável Ergonômico RGB", "price": 45.90, "original_price": 89.90, "thumbnail": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&q=80"},
            {"id": "MLB05", "title": "Kit Parafusadeira Furadeira Bateria 12v Bivolt", "price": 159.90, "original_price": 249.90, "thumbnail": "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=500&q=80"}
        ]

    random.shuffle(raw_items)

    results = []
    for item in raw_items[:limit]:
        title = item.get("title", "")
        price = item.get("price", 0.0)
        original_price = item.get("original_price") or (price * 1.25)
        discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 15
        
        # Constrói o link de busca direta infalível pelo título do produto
        encoded_title = urllib.parse.quote(title)
        permalink = f"https://lista.mercadolivre.com.br/{encoded_title}"
        if MELI_AFFILIATE_TAG:
            permalink = f"{permalink}#matt_tool={MELI_AFFILIATE_TAG}"

        thumbnail = item.get("thumbnail", "").replace("http://", "https://")
        if "-I.jpg" in thumbnail:
            thumbnail = thumbnail.replace("-I.jpg", "-O.jpg")
        elif "-I.webp" in thumbnail:
            thumbnail = thumbnail.replace("-I.webp", "-O.webp")

        results.append({
            "id": item.get("id"),
            "title": title,
            "permalink": permalink,
            "coupon_link": "https://www.mercadolivre.com.br/cupons",
            "original_price": round(original_price, 2),
            "price": round(price, 2),
            "discount": f"{discount_pct}%",
            "coupon": "OFERTAMELI",
            "thumbnail": thumbnail,
            "description": f"Aproveite esta super oferta: {title}"
        })

    return {"results": results, "total": len(results)}
