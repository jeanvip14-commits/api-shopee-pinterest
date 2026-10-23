import os
import time
import hashlib
import requests
from fastapi import FastAPI

app = FastAPI()

# As chaves serão lidas com segurança das Variáveis de Ambiente do Render
APP_KEY = os.getenv("18363460281")
APP_SECRET = os.getenv("BE6RSBISYSW4IRCATNFJHMUOBP7OMII7")

def generate_signature(payload_string, timestamp):
    base_string = f"{APP_KEY}{timestamp}{payload_string}{APP_SECRET}"
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

@app.get("/")
def home():
    return {"status": "API Shopee rodando de forma segura!"}

@app.get("/shopee-offers")
def get_shopee_offers():
    if not APP_KEY or not APP_SECRET:
        return {"error": "Chaves da Shopee não configuradas nas Variáveis de Ambiente!"}
        
    timestamp = int(time.time())
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    query = """
    query {
        productOfferV2(page: 1, limit: 10, sortType: 1) {
            nodes {
                itemId
                productName
                imageUrl
                price
                offerLink
            }
        }
    }
    """
    
    signature = generate_signature(query, timestamp)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_KEY}, Timestamp={timestamp}, Signature={signature}"
    }
    
    response = requests.post(url, json={"query": query}, headers=headers)
    return response.json()
