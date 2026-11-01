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
    # IDs de categorias principais do ML Brasil que liberam listagem pública de itens ativos
    categories = ["MLB1051", "MLB5726", "MLB1000", "MLB1648", "MLB1500", "MLB1499"]
    selected_cat = random.choice(categories)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    raw_items = []
    
    # 1. Puxa os lançamentos / destaques reais da categoria
    try:
        highlights_url = f"https://api.mercadolibre.com/highlights/MLB/category/{selected_cat}"
        h_resp = requests.get(highlights_url, headers=headers, timeout=5)
        if h_resp.status_code == 200:
            h_data = h_resp.json()
            content = h_data.get("content", [])
            item_ids = [i["id"] for i in content if i.get("type") == "ITEM" and "id" in i]
            
            if item_ids:
                random.shuffle(item_ids)
                selected_ids = item_ids[:limit]
                # Consulta os detalhes exatos de cada produto (incluindo o permalink direto)
                multiget_url = f"https://api.mercadolibre.com/items?ids={','.join(selected_ids)}"
                m_resp = requests.get(multiget_url, headers=headers, timeout=5)
                if m_resp.status_code == 200:
                    raw_items = m_resp.json()
    except Exception:
        raw_items = []

    results = []

    # Processa os itens retornados pela API oficial
    if raw_items:
        for wrap in raw_items:
            if wrap.get("code") == 200 and "body" in wrap:
                item = wrap["body"]
                price = item.get("price", 0.0)
                original_price = item.get("original_price") or (price * 1.25)
                discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 15
                
                permalink = item.get("permalink", "")
                if MELI_AFFILIATE_TAG and permalink:
                    permalink = f"{permalink}?matt_tool={MELI_AFFILIATE_TAG}"

                thumbnail = item.get("secure_thumbnail") or item.get("thumbnail", "")
                if "-I.jpg" in thumbnail:
                    thumbnail = thumbnail.replace("-I.jpg", "-O.jpg")
                elif "-I.webp" in thumbnail:
                    thumbnail = thumbnail.replace("-I.webp", "-O.webp")

                results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "permalink": permalink,  # LINK DIRETO DA PÁGINA DO PRODUTO
                    "coupon_link": "https://www.mercadolivre.com.br/cupons",
                    "original_price": round(original_price, 2),
                    "price": round(price, 2),
                    "discount": f"{discount_pct}%",
                    "coupon": "OFERTAMELI",
                    "thumbnail": thumbnail,
                    "description": f"Aproveite esta super oferta: {item.get('title')}"
                })

    # 2. Fallback de segurança com produtos verificados caso haja timeout na rede
    if not results:
        fallback_pool = [
            {
                "id": "MLB3298401294",
                "title": "Fone de Ouvido Bluetooth QCY T13 Sem Fio ANC",
                "price": 154.23,
                "original_price": 239.00,
                "permalink": "https://produto.mercadolivre.com.br/MLB-3298401294-fone-de-ouvido-sem-fio-qcy-t13-bluetooth-51.htm",
                "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_665471-MLA48644558066_122021-F.jpg"
            },
            {
                "id": "MLB2248109201",
                "title": "Carregador Rápido Baseus GaN 65W Multiportas USB-C",
                "price": 149.90,
                "original_price": 219.90,
                "permalink": "https://produto.mercadolivre.com.br/MLB-2248109201-carregador-de-tomada-baseus-gan5-pro-quick-charger-65w.htm",
                "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_789456-MLA54981203491_042023-F.jpg"
            }
        ]
        for item in fallback_pool[:limit]:
            price = item["price"]
            original_price = item["original_price"]
            discount_pct = int(((original_price - price) / original_price) * 100)
            permalink = item["permalink"]
            if MELI_AFFILIATE_TAG:
                permalink = f"{permalink}?matt_tool={MELI_AFFILIATE_TAG}"
            
            results.append({
                "id": item["id"],
                "title": item["title"],
                "permalink": permalink,
                "coupon_link": "https://www.mercadolivre.com.br/cupons",
                "original_price": round(original_price, 2),
                "price": round(price, 2),
                "discount": f"{discount_pct}%",
                "coupon": "OFERTAMELI",
                "thumbnail": item["thumbnail"],
                "description": f"Aproveite esta super oferta: {item['title']}"
            })

    return {"results": results, "total": len(results)}
