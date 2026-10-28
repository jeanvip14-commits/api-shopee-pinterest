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

# Credenciais Mercado Livre
MELI_APP_ID = os.getenv("MELI_APP_ID", "").strip()
MELI_CLIENT_SECRET = os.getenv("MELI_CLIENT_SECRET", "").strip()

def generate_shopee_signature(payload_str, timestamp):
    base_string = f"{SHOPEE_APP_KEY}{timestamp}{payload_str}{SHOPEE_APP_SECRET}"
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

def get_meli_access_token():
    """Gera token via Client Credentials com as credenciais oficiais da aplicação"""
    if not MELI_APP_ID or not MELI_CLIENT_SECRET:
        return None
        
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": MELI_APP_ID,
        "client_secret": MELI_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get("access_token")
    except Exception:
        pass
    return None

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
    limit: int = Query(50, description="Quantidade de produtos")
):
    token = get_meli_access_token()
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    results = []
    
    # 1. Consulta itens mais visitados/em destaque da categoria principal (Ferramentas/Casa - MLB1051)
    highlights_url = f"https://api.mercadolibre.com/highlights/MLB/category/MLB1051"
    
    try:
        resp = requests.get(highlights_url, headers=headers, timeout=12)
        if resp.status_code == 200:
            content = resp.json()
            items_list = content.get("content", [])
            
            # Extrai os IDs dos produtos retornados
            item_ids = [item.get("id") for item in items_list if item.get("type") == "item" and item.get("id")][:limit]
            
            if item_ids:
                # Consulta os detalhes multietapa de cada item diretamente
                ids_str = ",".join(item_ids[:20])  # Lote de até 20 itens por requisição
                details_url = f"https://api.mercadolibre.com/items?ids={ids_str}"
                
                resp_details = requests.get(details_url, headers=headers, timeout=12)
                if resp_details.status_code == 200:
                    details_data = resp_details.json()
                    for doc in details_data:
                        if doc.get("code") == 200:
                            body = doc.get("body", {})
                            results.append({
                                "id": body.get("id"),
                                "title": body.get("title"),
                                "permalink": body.get("permalink"),
                                "price": body.get("price"),
                                "thumbnail": body.get("secure_thumbnail") or body.get("thumbnail"),
                                "description": f"Confira a oferta: {body.get('title')} por R$ {body.get('price')}"
                            })
                            
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}
