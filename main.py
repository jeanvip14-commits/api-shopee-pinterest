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
    category: str = Query("todas", description="Categoria do produto"),
    limit: int = Query(8, description="Quantidade de produtos a retornar")
):
    # Catálogo com URLs válidas para evitar erros no Make/Pinterest
    catalog = {
        "ferramentas": [
            {
                "id": "MLB001",
                "title": "Bolsa Maleta Organizadora de Ferramentas Lona Impermeável",
                "original_price": 319.90, "price": 239.00, "discount": "25%", "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1581147036324-c17ac41dfa6c?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB002",
                "title": "Kit Parafusadeira Furadeira Bateria 12v Bivolt",
                "original_price": 249.90, "price": 159.90, "discount": "36%", "coupon": "FERRAMENTA10",
                "thumbnail": "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB003",
                "title": "Jogo de Ferramentas Manuais Profissionais 110 Peças com Maleta",
                "original_price": 259.90, "price": 189.90, "discount": "27%", "coupon": "OFERTAMELI",
                "thumbnail": "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB004",
                "title": "Serra Tico Tico 400w Profissional + Lâminas",
                "original_price": 199.90, "price": 139.90, "discount": "30%", "coupon": "CUPOMMELE",
                "thumbnail": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB005",
                "title": "Jogo Soquetes Catraca Reversível 40 peças Aço",
                "original_price": 89.90, "price": 55.90, "discount": "38%", "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1581147036324-c17ac41dfa6c?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB006",
                "title": "Kit Brocas e Pontas Titanium Furadeira 50 Peças",
                "original_price": 150.00, "price": 99.90, "discount": "33%", "coupon": "OFERTAMELI",
                "thumbnail": "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ],
        "casa": [
            {
                "id": "MLB101",
                "title": "Cesto De Roupa Suja Bambu 72L Dobravel Organizador",
                "original_price": 99.99, "price": 55.99, "discount": "44%", "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB102",
                "title": "Mop Giratório Limpeza Prática com Balde Centrifugador Inox",
                "original_price": 159.90, "price": 89.90, "discount": "43%", "coupon": "CASACOMDESC",
                "thumbnail": "https://images.unsplash.com/photo-1563453392212-326f5e854473?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB103",
                "title": "Kit com 2 Travesseiros Antialérgico Soft Coton 50X70cm",
                "original_price": 69.00, "price": 38.00, "discount": "45%", "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1505693314120-0d443867891c?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB104",
                "title": "Jogo de Panelas Antiaderente 5 Peças Cerâmica",
                "original_price": 299.90, "price": 189.90, "discount": "36%", "coupon": "OFERTAMELI",
                "thumbnail": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB105",
                "title": "Organizador de Sapatos Sapateira Dobrável",
                "original_price": 120.00, "price": 79.90, "discount": "33%", "coupon": "CASACOMDESC",
                "thumbnail": "https://images.unsplash.com/photo-1595341888016-a392ef81b7de?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB106",
                "title": "Varal de Chão Dobrável Aço Reforçado",
                "original_price": 150.00, "price": 99.90, "discount": "33%", "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ],
        "tecnologia": [
            {
                "id": "MLB201",
                "title": "Fone de Ouvido Bluetooth Sem Fio Ruído Ativo ANC",
                "original_price": 299.00, "price": 189.00, "discount": "37%", "coupon": "TECHMELI",
                "thumbnail": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB202",
                "title": "Carregador Rápido GaN 65W Multiportas USB-C",
                "original_price": 199.90, "price": 129.90, "discount": "35%", "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB203",
                "title": "Smartwatch Relógio Inteligente Esportivo Bip",
                "original_price": 350.00, "price": 219.00, "discount": "37%", "coupon": "OFERTAMELI",
                "thumbnail": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB204",
                "title": "Mouse Sem Fio Recarregável Ergonômico RGB",
                "original_price": 89.90, "price": 45.90, "discount": "49%", "coupon": "TECHMELI",
                "thumbnail": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB205",
                "title": "Ring Light LED de Mesa com Tripé para Lives",
                "original_price": 120.00, "price": 65.00, "discount": "45%", "coupon": "MELISUPERCLUB",
                "thumbnail": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            },
            {
                "id": "MLB206",
                "title": "Caixa de Som Bluetooth Impermeável Portátil",
                "original_price": 210.00, "price": 135.00, "discount": "35%", "coupon": "OFERTAMELI",
                "thumbnail": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80",
                "permalink": "https://mercadolivre.com/sec/2ZC3xKD", "coupon_link": "https://www.mercadolivre.com.br/cupons"
            }
        ]
    }
    
    cat_key = category.lower().strip() if category else "todas"
    selected_items = []
    
    if cat_key in ["todas", "mix", "all"]:
        all_products = []
        for key in catalog:
            all_products.extend(catalog[key])
        selected_items = all_products
    elif cat_key in catalog:
        selected_items = list(catalog[cat_key])
    else:
        selected_items = list(catalog["ferramentas"])
        
    random.shuffle(selected_items)
        
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
