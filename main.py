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
    # Catálogo de ofertas com links diretos de afiliado (formato meli.la / sec)
    # Subtitua os links pelas suas URLs geradas no painel de afiliados Mercado Livre
    affiliate_offers = [
        {
            "id": "MLB001",
            "title": "Kit 2 Travesseiros Antialérgico Soft Coton 50x70cm Branco",
            "price": 38.00,
            "original_price": 69.00,
            "permalink": "https://meli.la/2ZC3xKD",  # Insira aqui o seu link gerado meli.la
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_897120-MLA50918239012_072022-F.jpg"
        },
        {
            "id": "MLB002",
            "title": "Fone de Ouvido Bluetooth QCY T13 Sem Fio ANC",
            "price": 154.23,
            "original_price": 239.00,
            "permalink": "https://meli.la/2ZC3xKD",  # Substitua pelo seu link meli.la deste produto
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_665471-MLA48644558066_122021-F.jpg"
        },
        {
            "id": "MLB003",
            "title": "Smartwatch Relógio Inteligente Amazfit Bip 5 GPS",
            "price": 389.00,
            "original_price": 499.00,
            "permalink": "https://meli.la/2ZC3xKD",  # Substitua pelo seu link meli.la deste produto
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_897521-MLA71295248102_082023-F.jpg"
        },
        {
            "id": "MLB004",
            "title": "Carregador Rápido Baseus GaN 65W Multiportas USB-C",
            "price": 129.90,
            "original_price": 199.90,
            "permalink": "https://meli.la/2ZC3xKD",  # Substitua pelo seu link meli.la deste produto
            "thumbnail": "https://http2.mlstatic.com/D_NQ_NP_2X_789456-MLA54981203491_042023-F.jpg"
        },
        {
            "id": "MLB005",
            "title": "Mouse Sem Fio Ergonômico Recarregável RGB",
            "price": 45.90,
            "original_price": 89.90,
            "permalink": "https://meli.la/2ZC3xKD",  # Substitua pelo seu link meli.la deste produto
            "thumbnail": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&q=80"
        }
    ]

    # Seleciona ofertas aleatórias para diversificar as postagens
    selected_items = random.sample(affiliate_offers, min(limit, len(affiliate_offers)))

    results = []
    for item in selected_items:
        price = item.get("price", 0.0)
        original_price = item.get("original_price") or (price * 1.25)
        discount_pct = int(((original_price - price) / original_price) * 100)

        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "permalink": item.get("permalink"),
            "coupon_link": "https://www.mercadolivre.com.br/cupons",
            "original_price": round(original_price, 2),
            "price": round(price, 2),
            "discount": f"{discount_pct}%",
            "coupon": "MELISUPERCLUB",
            "thumbnail": item.get("thumbnail"),
            "description": f"Aproveite esta super oferta: {item.get('title')}"
        })

    return {"results": results, "total": len(results)}
