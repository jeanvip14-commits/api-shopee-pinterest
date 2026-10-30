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
    category: str = Query("todas", description="Categoria do produto (ferramentas, casa, tecnologia, todas)"),
    limit: int = Query(8, description="Quantidade de produtos a retornar")
):
    # Catálogo com links de busca estruturados oficiais do Mercado Livre (nunca dão erro 404)
    catalog = {
        "ferramentas": [
            {
                "id": "MLB001",
                "title": "Bolsa Maleta Organizadora de Ferramentas Lona Impermeável",
                "price": 239.00,
                "thumbnail": "https://images.unsplash.com/photo-1581147036324-c17ac41dfa6c?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://lista.mercadolivre.com.br/bolsa-maleta-ferramentas-impermeavel",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB002",
                "title": "Bolsa Maleta Organizador de Ferramentas Lona Multifuncional",
                "price": 93.98,
                "thumbnail": "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://lista.mercadolivre.com.br/bolsa-maleta-ferramentas-multifuncional",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB003",
                "title": "Jogo de Ferramentas Manuais Profissionais 110 Peças com Maleta",
                "price": 189.90,
                "thumbnail": "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://lista.mercadolivre.com.br/jogo-de-ferramentas-110-pecas",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ],
        "casa": [
            {
                "id": "MLB101",
                "title": "Cesto De Roupa Suja Bambu 72L Dobravel Organizador Forrado Banheiro",
                "price": 55.99,
                "thumbnail": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://lista.mercadolivre.com.br/cesto-roupa-bambu-72l",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB102",
                "title": "Mop Giratório Limpeza Prática com Balde Centrifugador Inox",
                "price": 89.90,
                "thumbnail": "https://images.unsplash.com/photo-1563453392212-326f5e854473?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://lista.mercadolivre.com.br/mop-giratorio-balde-inox",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ],
        "tecnologia": [
            {
                "id": "MLB201",
                "title": "Fone de Ouvido Bluetooth Sem Fio Ruído Ativo ANC",
                "price": 189.00,
                "thumbnail": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://lista.mercadolivre.com.br/fone-bluetooth-anc",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB202",
                "title": "Carregador Rápido GaN 65W Multiportas USB-C e USB-A",
                "price": 129.90,
                "thumbnail": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://lista.mercadolivre.com.br/carregador-gan-65w",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ]
    }
    
    cat_key = category.lower().strip() if category else "todas"
    selected_items = []
    
    if cat_key in ["todas", "mix", "all"]:
        max_per_cat = max(1, limit // len(catalog))
        for key in catalog:
            selected_items.extend(catalog[key][:max_per_cat])
    elif cat_key in catalog:
        selected_items = catalog[cat_key]
    else:
        selected_items = catalog["ferramentas"]
        
    results = []
    for item in selected_items[:limit]:
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
