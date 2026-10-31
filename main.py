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
    # =====================================================================
    # SEU CATÁLOGO DE OFERTAS: SUBSTITUA OS DADOS ABAIXO PELOS SEUS REAIS
    # =====================================================================
    catalog = {
        "ferramentas": [
            {
                "id": "MLB001",
                "title": "NOME DO PRODUTO REAL 1",
                "original_price": 199.90, 
                "price": 99.90, 
                "discount": "50%", 
                "coupon": "SEUCUPOM1",
                "thumbnail": "LINK_DA_IMAGEM_REAL_1.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_1", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_1"
            },
            {
                "id": "MLB002",
                "title": "NOME DO PRODUTO REAL 2",
                "original_price": 299.90, 
                "price": 149.90, 
                "discount": "50%", 
                "coupon": "SEUCUPOM2",
                "thumbnail": "LINK_DA_IMAGEM_REAL_2.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_2", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_2"
            },
            {
                "id": "MLB003",
                "title": "NOME DO PRODUTO REAL 3",
                "original_price": 150.00, 
                "price": 100.00, 
                "discount": "33%", 
                "coupon": "SEUCUPOM3",
                "thumbnail": "LINK_DA_IMAGEM_REAL_3.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_3", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_3"
            }
        ],
        "casa": [
            {
                "id": "MLB101",
                "title": "NOME DO PRODUTO REAL 4",
                "original_price": 99.99, 
                "price": 55.99, 
                "discount": "44%", 
                "coupon": "SEUCUPOM4",
                "thumbnail": "LINK_DA_IMAGEM_REAL_4.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_4", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_4"
            },
            {
                "id": "MLB102",
                "title": "NOME DO PRODUTO REAL 5",
                "original_price": 159.90, 
                "price": 89.90, 
                "discount": "43%", 
                "coupon": "SEUCUPOM5",
                "thumbnail": "LINK_DA_IMAGEM_REAL_5.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_5", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_5"
            },
            {
                "id": "MLB103",
                "title": "NOME DO PRODUTO REAL 6",
                "original_price": 69.00, 
                "price": 38.00, 
                "discount": "45%", 
                "coupon": "SEUCUPOM6",
                "thumbnail": "LINK_DA_IMAGEM_REAL_6.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_6", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_6"
            }
        ],
        "tecnologia": [
            {
                "id": "MLB201",
                "title": "NOME DO PRODUTO REAL 7",
                "original_price": 299.00, 
                "price": 189.00, 
                "discount": "37%", 
                "coupon": "SEUCUPOM7",
                "thumbnail": "LINK_DA_IMAGEM_REAL_7.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_7", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_7"
            },
            {
                "id": "MLB202",
                "title": "NOME DO PRODUTO REAL 8",
                "original_price": 199.90, 
                "price": 129.90, 
                "discount": "35%", 
                "coupon": "SEUCUPOM8",
                "thumbnail": "LINK_DA_IMAGEM_REAL_8.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_8", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_8"
            },
            {
                "id": "MLB203",
                "title": "NOME DO PRODUTO REAL 9",
                "original_price": 350.00, 
                "price": 219.00, 
                "discount": "37%", 
                "coupon": "SEUCUPOM9",
                "thumbnail": "LINK_DA_IMAGEM_REAL_9.jpg",
                "permalink": "SEU_LINK_DE_AFILIADO_CURTO_9", 
                "coupon_link": "LINK_DA_PAGINA_DE_CUPONS_9"
            }
        ]
    }
    
    cat_key = category.lower().strip() if category else "todas"
    selected_items = []
    
    # Agrupar produtos
    if cat_key in ["todas", "mix", "all"]:
        all_products = []
        for key in catalog:
            all_products.extend(catalog[key])
        selected_items = all_products
    elif cat_key in catalog:
        selected_items = list(catalog[cat_key])
    else:
        selected_items = list(catalog["ferramentas"])
        
    # Baralhar a lista para não repetir a ordem
    random.shuffle(selected_items)
        
    results = []
    # Limitar aos itens solicitados (ex: 8)
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
