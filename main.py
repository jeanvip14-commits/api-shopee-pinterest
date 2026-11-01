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
    # Categorias oficiais do Mercado Livre Brasil com anúncios ativos em tempo real
    categories_mlb = [
        "MLB1051", # Celulares e Telefones
        "MLB5726", # Eletrodomésticos
        "MLB1000", # Eletrônicos, Áudio e Vídeo
        "MLB1648", # Informática
        "MLB1500", # Esportes e Fitness
        "MLB1499"  # Ferramentas e Indústria
    ]
    
    selected_cat = random.choice(categories_mlb)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    raw_items = []
    
    # 1. Puxa os IDs dos anúncios em destaque e ativos em tempo real
    try:
        h_url = f"https://api.mercadolibre.com/highlights/MLB/category/{selected_cat}"
        h_resp = requests.get(h_url, headers=headers, timeout=6)
        if h_resp.status_code == 200:
            content = h_resp.json().get("content", [])
            item_ids = [i["id"] for i in content if i.get("type") == "ITEM" and "id" in i]
            
            if item_ids:
                random.shuffle(item_ids)
                fetch_ids = item_ids[:limit]
                # Faz multiget oficial para extrair o permalink exato e atualizado do produto
                m_url = f"https://api.mercadolibre.com/items?ids={','.join(fetch_ids)}"
                m_resp = requests.get(m_url, headers=headers, timeout=6)
                if m_resp.status_code == 200:
                    raw_items = m_resp.json()
    except Exception:
        raw_items = []

    results = []

    if raw_items:
        for wrap in raw_items:
            if wrap.get("code") == 200 and "body" in wrap:
                item = wrap["body"]
                
                # Garante que o anúncio está ativo
                if item.get("status") != "active":
                    continue
                    
                price = item.get("price", 0.0)
                original_price = item.get("original_price") or (price * 1.25)
                discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 20
                
                # PERMALINK DIRETO DO PRODUTO ATIVO NO MERCADO LIVRE
                permalink = item.get("permalink", "")
                if MELI_AFFILIATE_TAG and permalink:
                    sep = "&" if "?" in permalink else "?"
                    permalink = f"{permalink}{sep}matt_tool={MELI_AFFILIATE_TAG}"

                # Imagem em alta definição
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

    # 2. Se a API pública do ML oscilar, tenta busca direta por itens ativos de tecnologia
    if not results:
        try:
            search_url = "https://api.mercadolibre.com/sites/MLB/search?category=MLB1051&limit=20"
            s_resp = requests.get(search_url, headers=headers, timeout=6)
            if s_resp.status_code == 200:
                search_results = s_resp.json().get("results", [])
                random.shuffle(search_results)
                for item in search_results[:limit]:
                    price = item.get("price", 0.0)
                    original_price = item.get("original_price") or (price * 1.25)
                    discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 20
                    permalink = item.get("permalink", "")
                    if MELI_AFFILIATE_TAG and permalink:
                        sep = "&" if "?" in permalink else "?"
                        permalink = f"{permalink}{sep}matt_tool={MELI_AFFILIATE_TAG}"
                    
                    thumbnail = item.get("thumbnail", "").replace("http://", "https://")
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
        except Exception:
            pass

    return {"results": results, "total": len(results)}
