import os
import time
import hashlib
import json
import requests
import re
import html
import xml.etree.ElementTree as ET
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
    rss_url = "https://lista.mercadolivre.com.br/ofertas_Rss-xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(rss_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": f"Erro Mercado Livre: {response.status_code}", "results": []}
            
        # Sanitização para remover caracteres inválidos do XML
        clean_xml = re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', response.text)
        clean_xml = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', clean_xml)
        
        root = ET.fromstring(clean_xml)
        results = []
        
        for item in root.findall("./channel/item")[:limit]:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            description = item.find("description").text if item.find("description") is not None else ""
            
            title = html.unescape(re.sub(r'<[^>]+>', '', title)).strip()
            description = html.unescape(re.sub(r'<[^>]+>', '', description)).strip()
            
            results.append({
                "title": title,
                "permalink": link,
                "description": description
            })
            
        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}
