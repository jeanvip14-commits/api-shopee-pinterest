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
    # Lista de IDs das principais categorias no Mercado Livre Brasil (MLB)
    categories_mlb = [
        "MLB1051", # Celulares e Telefones
        "MLB5726", # Eletrodomésticos
        "MLB1000", # Eletrônicos, Áudio e Vídeo
        "MLB1648", # Informática
        "MLB1500", # Esportes e Fitness
        "MLB5672", # Acessórios para Veículos
        "MLB1499"  # Indústria e Comércio (Ferramentas)
    ]
    
    # Define a categoria escolhida ou sorteia uma se for 'todas'
    cat_id = random.choice(categories_mlb)
    
    # Endpoint de destaques por categoria (funciona sem bloqueio de Cloudflare)
    url = f"https://api.mercadolibre.com/highlights/MLB/category/{cat_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    items_data = []
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            content = resp.json()
            # Extrai os IDs dos itens em destaque
            results_list = content.get("content", [])
            item_ids = [item["id"] for item in results_list if item.get("type") == "ITEM" and "id" in item]
            
            # Seleciona ate 'limit' itens aleatórios para buscar os detalhes
            random.shuffle(item_ids)
            selected_ids = item_ids[:limit]
            
            if selected_ids:
                # Consulta multiget dos detalhes dos itens reais
                ids_str = ",".join(selected_ids)
                details_url = f"https://api.mercadolibre.com/items?ids={ids_str}"
                details_resp = requests.get(details_url, headers=headers, timeout=8)
                if details_resp.status_code == 200:
                    items_data = details_resp.json()
    except Exception:
        items_data = []

    results = []
    for item_wrap in items_data:
        if item_wrap.get("code") == 200 and "body" in item_wrap:
            item = item_wrap["body"]
            
            price = item.get("price", 0.0)
            original_price = item.get("original_price") or (price * 1.20)
            discount_pct = int(((original_price - price) / original_price) * 100) if original_price > price else 15
            
            # Imagem de alta resolução
            thumbnail = item.get("secure_thumbnail") or item.get("thumbnail", "")
            if "-I.jpg" in thumbnail:
                thumbnail = thumbnail.replace("-I.jpg", "-O.jpg")
            elif "-I.webp" in thumbnail:
                thumbnail = thumbnail.replace("-I.webp", "-O.webp")

            results.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "permalink": item.get("permalink"), # LINK REAL DO PRODUTO NO MERCADO LIVRE
                "coupon_link": "https://www.mercadolivre.com.br/cupons",
                "original_price": round(original_price, 2),
                "price": round(price, 2),
                "discount": f"{discount_pct}%",
                "coupon": "OFERTAMELI",
                "thumbnail": thumbnail,
                "description": f"Aproveite esta super oferta: {item.get('title')}"
            })

    return {"results": results, "total": len(results)}
