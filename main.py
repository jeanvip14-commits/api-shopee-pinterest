import os
import time
import hashlib
import json
import requests
from fastapi import FastAPI, Query, Response

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

@app.get("/proxy-image")
def proxy_image(url: str):
    """
    Faz o download da imagem do CDN do Mercado Livre com cabeçalhos de browser
    e devolve os bytes diretamente. Resolve 100% o bloqueio de imagem no Telegram/Pinterest.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        return Response(content=resp.content, media_type="image/jpeg")
    except Exception as e:
        return Response(status_code=400, content=str(e))

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
    category: str = Query(None, description="Filtro de Categoria/Busca"),
    q: str = Query(None, description="Termo de busca alternativo"),
    limit: int = Query(10, description="Quantidade de produtos")
):
    """
    Busca produtos diretamente na API oficial de busca do Mercado Livre
    pelo termo passado em 'category' ou 'q' (semelhante à Shopee).
    """
    search_term = category or q or "ferramentas"
    target_url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term.strip()}&limit={limit}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    results = []
    render_base_url = "https://api-shopee-pinterest.onrender.com"
    
    try:
        resp = requests.get(target_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            raw_results = data.get("results", [])
            
            for item in raw_results:
                raw_thumb = item.get("secure_thumbnail") or item.get("thumbnail") or ""
                # Força formato em alta resolução (.JPG)
                if raw_thumb:
                    raw_thumb = raw_thumb.replace("-I.jpg", "-O.jpg").replace("-I.webp", "-O.jpg")
                
                # Passa a imagem pelo proxy para o Telegram conseguir exibir
                proxy_thumb = f"{render_base_url}/proxy-image?url={raw_thumb}" if raw_thumb else ""
                
                results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "permalink": item.get("permalink"),
                    "coupon_link": "https://www.mercadolivre.com.br/cupons",
                    "price": item.get("price"),
                    "thumbnail": proxy_thumb,
                    "description": f"Confira esta oferta no Mercado Livre: {item.get('title')} por R$ {item.get('price')}"
                })
    except Exception:
        pass
        
    return {"results": results, "total": len(results)}
