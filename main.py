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
    # IDs das principais categorias oficiais do Mercado Livre Brasil
    categories = [
        "MLB1051", # Celulares e Telefones
        "MLB5726", # Eletrodomésticos
        "MLB1000", # Eletrônicos, Áudio e Vídeo
        "MLB1648", # Informática
        "MLB1500", # Esportes e Fitness
        "MLB1499"  # Ferramentas e Indústria
    ]
    
    selected_cat = random.choice(categories)
    
    # Endpoint de tendências / mais vendidos por categoria (não exige OAuth e não bloqueia IP de servidor)
    url = f"https://api.mercadolibre.com/trends/MLB/{selected_cat}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    items_list = []
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            trends = resp.json()
            # Pega as palavras de tendência e busca pelos itens diretos
            if isinstance(trends, list) and len(trends) > 0:
                keyword = random.choice(trends).get("keyword", "ofertas")
                search_url = f"https://api.mercadolibre.com/sites/MLB/search?q={keyword}&limit=30"
                s_resp = requests.get(search_url, headers=headers, timeout=8)
                if s_resp.status_code == 200:
                    items_list = s_resp.json().get("results", [])
    except Exception:
        items_list = []

    # Fallback dinâmico buscando por ofertas globais caso o endpoint de tendências falhe
    if not items_list:
        try:
            direct_url = "https://api.mercadolibre.com/sites/MLB/search?q=promo&limit=30"
            d_resp = requests.get(direct_url, headers=headers, timeout=8)
            if d_resp.status_code == 200:
                items_list = d_resp.json().get("results", [])
        except Exception:
            items_list = []

    # Filtra produtos válidos que possuem título e permalink real
    valid_products = [p for p in items_list if p.get("permalink") and p.get("title")]

    if not valid_products:
        return {"results": [], "total": 0}

    random.shuffle(valid_products)

    results = []
    for item in valid_products[:limit]:
        price = item.get("price", 0.0)
        original_price = item.get("original_price") or (price * 1.25)
        
        discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 20
        
        # Ajusta imagem para alta definição e HTTPS
        thumbnail = item.get("thumbnail", "").replace("http://", "https://")
        if "-I.jpg" in thumbnail:
            thumbnail = thumbnail.replace("-I.jpg", "-O.jpg")
        elif "-I.webp" in thumbnail:
            thumbnail = thumbnail.replace("-I.webp", "-O.webp")

        # PERMALINK REAL DO PRODUTO (ex: https://produto.mercadolivre.com.br/MLB-...)
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
