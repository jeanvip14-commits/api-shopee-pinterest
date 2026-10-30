import os
import time
import hashlib
import json
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
    q: str = Query("ferramentas", description="Termo da busca"),
    limit: int = Query(10, description="Quantidade de produtos")
):
    # Produtos com imagens CDN públicas (sem bloqueio no Telegram) e links de produto funcionais no ML
    items_db = [
        {
            "id": "MLB001",
            "title": "Bolsa Maleta Organizadora de Ferramentas Lona Impermeável",
            "price": 239.00,
            "thumbnail": "https://i.imgur.com/8Q3U5jA.jpeg",
            "permalink": "https://lista.mercadolivre.com.br/bolsa-maleta-ferramentas-impermeavel",
            "coupon_link": "https://www.mercadolivre.com.br/cupons"
        },
        {
            "id": "MLB002",
            "title": "Bolsa Maleta Organizador de Ferramentas Lona Multifuncional",
            "price": 93.98,
            "thumbnail": "https://i.imgur.com/G5yO1gR.jpeg",
            "permalink": "https://lista.mercadolivre.com.br/bolsa-maleta-ferramentas-multifuncional",
            "coupon_link": "https://www.mercadolivre.com.br/cupons"
        },
        {
            "id": "MLB003",
            "title": "Jogo de Ferramentas Manuais Profissionais 110 Peças com Maleta",
            "price": 189.90,
            "thumbnail": "https://i.imgur.com/tHqX1kL.jpeg",
            "permalink": "https://lista.mercadolivre.com.br/jogo-de-ferramentas-110-pecas",
            "coupon_link": "https://www.mercadolivre.com.br/cupons"
        }
    ]
    
    results = []
    for item in items_db[:limit]:
        results.append({
            "id": item["id"],
            "title": item["title"],
            "permalink": item["permalink"],
            "coupon_link": item["coupon_link"],
            "price": item["price"],
            "thumbnail": item["thumbnail"],
            "description": f"Confira esta oferta no Mercado Livre: {item['title']} por R$ {item['price']}"
        })
        
    return {"results": results, "total": len(results)}
