import os
import time
import hashlib
import json
import requests
from bs4 import BeautifulSoup
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
    # RSS de ofertas do Mercado Livre
    rss_url = "https://lista.mercadolivre.com.br/ofertas_Rss-xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(rss_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": f"Erro Mercado Livre: {response.status_code}", "results": []}
            
        # BeautifulSoup com parser XML lê o RSS perfeitamente mesmo com tags mal formatadas
        soup = BeautifulSoup(response.text, "xml")
        items = soup.find_all("item")
        
        results = []
        for item in items[:limit]:
            title = item.find("title").text.strip() if item.find("title") else ""
            link = item.find("link").text.strip() if item.find("link") else ""
            description = item.find("description").text.strip() if item.find("description") else ""
            
            results.append({
                "title": title,
                "permalink": link,
                "description": description
            })
            
        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}
