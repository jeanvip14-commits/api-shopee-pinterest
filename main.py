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
    # A Shopee exige a concatenação: APP_KEY + timestamp + payload + APP_SECRET
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
    
    # Query GraphQL dinâmica utilizando os parâmetros page e limit
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

# Nova rota criada para contornar o bloqueio de IP do Mercado Livre
@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ofertas", description="Termo de busca"),
    limit: int = Query(30, description="Quantidade de produtos (máx 50)")
):
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={q}&limit={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
