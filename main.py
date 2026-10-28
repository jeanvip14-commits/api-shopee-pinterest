import os
import time
import hashlib
import json
import requests
from fastapi import FastAPI, Query

app = FastAPI()

APP_KEY = os.getenv("SHOPEE_APP_KEY", "").strip()
APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "").strip()

def generate_signature(payload_str, timestamp):
    base_string = f"{APP_KEY}{timestamp}{payload_str}{APP_SECRET}"
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

@app.get("/")
def home():
    return {"status": "API Shopee e Mercado Livre a rodar de forma segura!"}

@app.get("/shopee-offers")
def get_shopee_offers(
    page: int = Query(1, description="Número da página"),
    limit: int = Query(100, description="Quantidade de produtos por busca (máx 100)")
):
    if not APP_KEY or not APP_SECRET:
        return {"error": "Chaves da Shopee nao configuradas nas Variaveis de Ambiente!"}
        
    timestamp = int(time.time())
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    query_str = f"query{{productOfferV2(page:{page},limit:{limit},sortType:1){{nodes{{itemId,productName,imageUrl,price,offerLink}}}}}}"
    payload = {"query": query_str}
    payload_json_compact = json.dumps(payload, separators=(',', ':'))
    
    signature = generate_signature(payload_json_compact, timestamp)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_KEY}, Timestamp={timestamp}, Signature={signature}"
    }
    
    response = requests.post(url, data=payload_json_compact, headers=headers)
    return response.json()

@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ofertas", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    # Utiliza o endpoint de Tendências e Categoria Destaque do Mercado Livre (não sofre bloqueio IP)
    trends_url = "https://api.mercadolibre.com/trends/MLB"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    results = []
    try:
        # Busca os termos/produtos em alta
        resp_trends = requests.get(trends_url, headers=headers, timeout=10)
        
        if resp_trends.status_code == 200:
            trends_data = resp_trends.json()
            # Pega as primeiras palavras/produtos mais buscados
            for item in trends_data[:limit]:
                keyword = item.get("keyword", "")
                url_item = item.get("url", "")
                if keyword:
                    results.append({
                        "id": keyword,
                        "title": f"Oferta em Destaque: {keyword.capitalize()}",
                        "permalink": url_item if url_item else f"https://lista.mercadolivre.com.br/{keyword}",
                        "price": 0,
                        "description": f"Confira as melhores ofertas para {keyword} no Mercado Livre!"
                    })

        # Fallback: Caso as tendências falhem, consulta categorias principais sem IP blocking
        if not results:
            cat_url = "https://api.mercadolibre.com/sites/MLB/categories"
            resp_cat = requests.get(cat_url, headers=headers, timeout=10)
            if resp_cat.status_code == 200:
                for cat in resp_cat.json()[:limit]:
                    results.append({
                        "id": cat.get("id"),
                        "title": f"Ofertas na Categoria: {cat.get('name')}",
                        "permalink": f"https://lista.mercadolivre.com.br/{cat.get('name')}",
                        "price": 0,
                        "description": f"Encontre promoções imperdíveis na categoria {cat.get('name')}!"
                    })

        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}
