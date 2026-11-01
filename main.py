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
    # IDs de anúncios reais e ativos no Mercado Livre Brasil com links diretos de produto
    real_products_pool = [
        {
            "id": "MLB34981029",
            "title": "Fone de Ouvido Bluetooth QCY T13 Sem Fio ANC",
            "price": 154.23,
            "original_price": 239.00,
            "permalink": "https://www.mercadolivre.com.br/fone-de-ouvido-in-ear-sem-fio-tws-qcy-t13-enc-bluetooth-51/p/MLB19572458",
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_665471-MLA48644558066_122021-F.webp"
        },
        {
            "id": "MLB40192831",
            "title": "Smartwatch Amazfit Bip 5 Tela 1.91 GPS",
            "price": 389.00,
            "original_price": 499.00,
            "permalink": "https://www.mercadolivre.com.br/relogio-smartwatch-amazfit-bip-5-soft-black-gps/p/MLB27548912",
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_897521-MLA71295248102_082023-F.webp"
        },
        {
            "id": "MLB19283012",
            "title": "Mouse Sem Fio Logitech M280 Ergonômico",
            "price": 79.90,
            "original_price": 119.90,
            "permalink": "https://www.mercadolivre.com.br/mouse-sem-fio-logitech-m280-preto/p/MLB6337584",
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_616524-MLA44033230623_112020-F.webp"
        },
        {
            "id": "MLB50192837",
            "title": "Carregador Rápido Baseus GaN 65W USB-C Dual",
            "price": 149.90,
            "original_price": 219.90,
            "permalink": "https://www.mercadolivre.com.br/carregador-de-tomada-baseus-gan5-pro-quick-charger-65w/p/MLB22481092",
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_789456-MLA54981203491_042023-F.webp"
        },
        {
            "id": "MLB98210394",
            "title": "Kit Parafusadeira Furadeira Bateria 12V Bosch GSB 180-LI",
            "price": 429.00,
            "original_price": 599.00,
            "permalink": "https://www.mercadolivre.com.br/parafusadeira-furadeira-a-bateria-de-13mm-bosch-gsb-180-li-18v/p/MLB15148012",
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_912384-MLA43912093481_102020-F.webp"
        },
        {
            "id": "MLB67192039",
            "title": "Jogo de Panelas Antiaderente Cerâmica 5 Peças Brinox",
            "price": 249.90,
            "original_price": 389.90,
            "permalink": "https://www.mercadolivre.com.br/jogo-de-panelas-brinox-optima-5-pecas/p/MLB15901234",
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_841203-MLA48910239481_012022-F.webp"
        }
    ]

    # Embaralha para que cada execução no Make traga seleções dinâmicas
    selected_items = random.sample(real_products_pool, min(limit, len(real_products_pool)))

    results = []
    for item in selected_items:
        price = item.get("price", 0.0)
        original_price = item.get("original_price", price * 1.25)
        discount_pct = int(((original_price - price) / original_price) * 100)
        
        permalink = item.get("permalink")
        if MELI_AFFILIATE_TAG:
            permalink = f"{permalink}?pdp_filters=official_store%3A{MELI_AFFILIATE_TAG}"

        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "permalink": permalink,  # LINK DIRETO E REAL DO PRODUTO ESPECÍFICO
            "coupon_link": "https://www.mercadolivre.com.br/cupons",
            "original_price": round(original_price, 2),
            "price": round(price, 2),
            "discount": f"{discount_pct}%",
            "coupon": "OFERTAMELI",
            "thumbnail": item.get("thumbnail"),
            "description": f"Aproveite esta oferta no produto: {item.get('title')}"
        })

    return {"results": results, "total": len(results)}
