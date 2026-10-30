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
    category: str = Query("todas", description="Categoria do produto (ferramentas, casa, tecnologia, todas)"),
    limit: int = Query(8, description="Quantidade de produtos a retornar")
):
    # Catálogo expandido de produtos para o sorteio dinâmico
    catalog = {
        "ferramentas": [
            {
                "id": "MLB001",
                "title": "Bolsa Maleta Organizadora de Ferramentas Lona Impermeável",
                "original_price": 319.90,
                "price": 239.00,
                "discount": "25%",
                "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1581147036324-c17ac41dfa6c?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB002",
                "title": "Bolsa Maleta Organizador de Ferramentas Lona Multifuncional",
                "original_price": 149.90,
                "price": 93.98,
                "discount": "37%",
                "coupon": "CUPOMMELE",
                "thumbnail": "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB003",
                "title": "Jogo de Ferramentas Manuais Profissionais 110 Peças com Maleta",
                "original_price": 259.90,
                "price": 189.90,
                "discount": "27%",
                "coupon": "OFERTAMELI",
                "thumbnail": "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ],
        "casa": [
            {
                "id": "MLB101",
                "title": "Cesto De Roupa Suja Bambu 72L Dobravel Organizador Forrado Banheiro",
                "original_price": 99.99,
                "price": 55.99,
                "discount": "44%",
                "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB102",
                "title": "Mop Giratório Limpeza Prática com Balde Centrifugador Inox",
                "original_price": 159.90,
                "price": 89.90,
                "discount": "43%",
                "coupon": "CASACOMDESC",
                "thumbnail": "https://images.unsplash.com/photo-1563453392212-326f5e854473?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ],
        "tecnologia": [
            {
                "id": "MLB201",
                "title": "Fone de Ouvido Bluetooth Sem Fio Ruído Ativo ANC",
                "original_price": 299.00,
                "price": 189.00,
                "discount": "37%",
                "coupon": "TECHMELI",
                "thumbnail": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB202",
                "title": "Carregador Rápido GaN 65W Multiportas USB-C e USB-A",
                "original_price": 199.90,
                "price": 129.90,
                "discount": "35%",
                "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=1000&auto=format&fit=crop&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD",
                "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ]
    }
    
    cat_key = category.lower().strip() if category else "todas"
    selected_items = []
    
    if cat_key in ["todas", "mix", "all"]:
        # Junta todos os produtos de todas as categorias e baralha aleatoriamente
        all_products = []
        for key in catalog:
            all_products.extend(catalog[key])
        random.shuffle(all_products)
        selected_items = all_products
    elif cat_key in catalog:
        cat_list = list(catalog[cat_key])
        random.shuffle(cat_list)
        selected_items = cat_list
    else:
        cat_list = list(catalog["ferramentas"])
        random.shuffle(cat_list)
        selected_items = cat_list
        
    results = []
    for item in selected_items[:limit]:
        results.append({
            "id": item["id"],
            "title": item["title"],
            "permalink": item["permalink"],
            "coupon_link": item["coupon_link"],
            "original_price": item["original_price"],
            "price": item["price"],
            "discount": item["discount"],
            "coupon": item["coupon"],
            "thumbnail": item["thumbnail"],
            "description": f"Aproveite esta super oferta: {item['title']}"
        })
        
    return {"results": results, "total": len(results)}
