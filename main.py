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
    # Categorias mais vendidas do Mercado Livre Brasil
    categories_mlb = [
        "MLB1051",  # Celulares e Telefones
        "MLB5726",  # Eletrodomésticos
        "MLB1000",  # Eletrônicos, Áudio e Vídeo
        "MLB1648",  # Informática
        "MLB1500",  # Esportes e Fitness
        "MLB1499"   # Ferramentas
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    raw_items = []
    selected_cat = random.choice(categories_mlb)

    # 1. Busca produtos mais vendidos/em alta diretamente na categoria
    try:
        search_url = f"https://api.mercadolibre.com/sites/MLB/search?category={selected_cat}&sort=sold_quantity_desc&limit=40"
        resp = requests.get(search_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            raw_items = resp.json().get("results", [])
    except Exception:
        raw_items = []

    # 2. Se a categoria sorteada falhar, busca ofertas globais mais vendidas
    if not raw_items:
        try:
            fallback_url = "https://api.mercadolibre.com/sites/MLB/search?q=ofertas&sort=sold_quantity_desc&limit=40"
            resp_fb = requests.get(fallback_url, headers=headers, timeout=6)
            if resp_fb.status_code == 200:
                raw_items = resp_fb.json().get("results", [])
        except Exception:
            raw_items = []

    results = []

    # Embaralha para variar as postagens a cada execução
    random.shuffle(raw_items)

    for item in raw_items:
        if len(results) >= limit:
            break

        # Validação estrita: produto precisa ter link válido, preço > 0 e estoque ativo
        permalink = item.get("permalink", "")
        title = item.get("title", "")
        price = item.get("price", 0.0)
        available_qty = item.get("available_quantity", 1)

        if not permalink or not title or price <= 0 or available_qty <= 0:
            continue

        original_price = item.get("original_price") or (price * 1.25)
        discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 15

        # Injeta a tag de afiliado no link do anúncio oficial
        if MELI_AFFILIATE_TAG:
            sep = "&" if "?" in permalink else "?"
            permalink = f"{permalink}{sep}matt_tool={MELI_AFFILIATE_TAG}"

        # Ajusta imagem para alta definição
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
            "description": f"Aproveite esta super oferta em alta: {title}"
        })

    return {"results": results, "total": len(results)}
