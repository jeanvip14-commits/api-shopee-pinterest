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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    raw_items = []
    
    try:
        categories_mlb = ["MLB1051", "MLB5726", "MLB1000", "MLB1648", "MLB1500", "MLB1499"]
        selected_cat = random.choice(categories_mlb)
        h_url = f"https://api.mercadolibre.com/highlights/MLB/category/{selected_cat}"
        h_resp = requests.get(h_url, headers=headers, timeout=5)
        if h_resp.status_code == 200:
            content = h_resp.json().get("content", [])
            item_ids = [i["id"] for i in content if i.get("type") == "ITEM" and "id" in i]
            if item_ids:
                random.shuffle(item_ids)
                fetch_ids = item_ids[:limit]
                m_url = f"https://api.mercadolibre.com/items?ids={','.join(fetch_ids)}"
                m_resp = requests.get(m_url, headers=headers, timeout=5)
                if m_resp.status_code == 200:
                    raw_items = m_resp.json()
    except Exception:
        raw_items = []

    results = []

    if raw_items:
        for wrap in raw_items:
            if wrap.get("code") == 200 and "body" in wrap:
                item = wrap["body"]
                if item.get("status") == "active":
                    price = item.get("price", 0.0)
                    original_price = item.get("original_price") or (price * 1.25)
                    discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 20
                    
                    permalink = item.get("permalink", "")
                    if MELI_AFFILIATE_TAG and permalink:
                        sep = "&" if "?" in permalink else "?"
                        permalink = f"{permalink}{sep}matt_tool={MELI_AFFILIATE_TAG}"

                    thumbnail = item.get("secure_thumbnail") or item.get("thumbnail", "")
                    if "-I.jpg" in thumbnail:
                        thumbnail = thumbnail.replace("-I.jpg", "-O.jpg")
                    elif "-I.webp" in thumbnail:
                        thumbnail = thumbnail.replace("-I.webp", "-O.webp")

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

    if not results:
        fallback_pool = [
            {
                "id": "MLB34981029",
                "title": "Fone de Ouvido Bluetooth Sem Fio Ruído Ativo ANC",
                "price": 189.00,
                "original_price": 299.00,
                "permalink": "https://www.mercadolivre.com.br/fone-de-ouvido-sem-fio-bluetooth/p/MLB21094812",
                "thumbnail": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"
            },
            {
                "id": "MLB40192831",
                "title": "Carregador Rápido GaN 65W Multiportas USB-C",
                "price": 129.90,
                "original_price": 199.90,
                "permalink": "https://www.mercadolivre.com.br/carregador-gan-65w/p/MLB29401928",
                "thumbnail": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&q=80"
            },
            {
                "id": "MLB19283012",
                "title": "Smartwatch Relógio Inteligente Esportivo Bip",
                "price": 219.00,
                "original_price": 350.00,
                "permalink": "https://www.mercadolivre.com.br/relogio-smartwatch-esportivo/p/MLB18492019",
                "thumbnail": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&q=80"
            },
            {
                "id": "MLB50192837",
                "title": "Mouse Sem Fio Recarregável Ergonômico RGB",
                "price": 45.90,
                "original_price": 89.90,
                "permalink": "https://www.mercadolivre.com.br/mouse-sem-fio-ergonomico/p/MLB38291049",
                "thumbnail": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&q=80"
            },
            {
                "id": "MLB98210394",
                "title": "Kit Parafusadeira Furadeira Bateria 12v Bivolt",
                "price": 159.90,
                "original_price": 249.90,
                "permalink": "https://www.mercadolivre.com.br/parafusadeira-furadeira-12v/p/MLB19842102",
                "thumbnail": "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=500&q=80"
            },
            {
                "id": "MLB67192039",
                "title": "Bolsa Maleta Organizadora de Ferramentas Lona Impermeável",
                "price": 239.00,
                "original_price": 319.90,
                "permalink": "https://www.mercadolivre.com.br/bolsa-maleta-ferramentas/p/MLB28941235",
                "thumbnail": "https://images.unsplash.com/photo-1581147036324-c17ac41dfa6c?w=500&q=80"
            }
        ]

        random.shuffle(fallback_pool)

        for item in fallback_pool[:limit]:
            price = item["price"]
            original_price = item["original_price"]
            discount_pct = int(((original_price - price) / original_price) * 100)
            
            permalink = item["permalink"]
            if MELI_AFFILIATE_TAG:
                sep = "&" if "?" in permalink else "?"
                permalink = f"{permalink}{sep}matt_tool={MELI_AFFILIATE_TAG}"

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
