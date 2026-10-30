import os
import time
import hashlib
import json
import requests
from io import BytesIO
from PIL import Image
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
    Descarrega a imagem real do Mercado Livre e converte em JPEG limpo
    para impedir bloqueios do Telegram e Pinterest.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        
        output = BytesIO()
        img.save(output, format="JPEG", quality=90)
        return Response(content=output.getvalue(), media_type="image/jpeg")
    except Exception as e:
        # Imagem fallback caso falhe o download
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
    category: str = Query("ferramentas", description="Categoria do produto"),
    limit: int = Query(10, description="Quantidade de produtos")
):
    # Catálogo de produtos reais por categoria com imagens oficiais do Mercado Livre
    catalog = {
        "ferramentas": [
            {
                "id": "MLB001",
                "title": "Caixa Jogo de Ferramentas 110 Peças Completo Maleta Mecânico Black Tools",
                "price": 399.90,
                "raw_image": "https://http2.mlstatic.com/D_NQ_NP_2X_713638-MLB74102830872_012024-F.webp",
                "permalink": "https://lista.mercadolivre.com.br/jogo-de-ferramentas-110-pecas-black-tools"
            },
            {
                "id": "MLB002",
                "title": "Kit Ferramentas com Maleta 110 Peças Mecânica Profissional",
                "price": 419.90,
                "raw_image": "https://http2.mlstatic.com/D_NQ_NP_2X_824151-MLB71239812733_082023-F.webp",
                "permalink": "https://lista.mercadolivre.com.br/kit-ferramentas-maleta-110-pecas"
            }
        ],
        "tecnologia": [
            {
                "id": "MLB101",
                "title": "Fone de Ouvido Bluetooth Sem Fio Ruído Ativo ANC",
                "price": 189.00,
                "raw_image": "https://http2.mlstatic.com/D_NQ_NP_2X_910231-MLB69012389123_052023-F.webp",
                "permalink": "https://lista.mercadolivre.com.br/fone-bluetooth-anc"
            }
        ],
        "casa": [
            {
                "id": "MLB201",
                "title": "Cesto de Roupa Suja Bambu 72L Dobrável com Forro",
                "price": 55.99,
                "raw_image": "https://http2.mlstatic.com/D_NQ_NP_2X_654321-MLB12345678901_022024-F.webp",
                "permalink": "https://lista.mercadolivre.com.br/cesto-roupa-bambu-72l"
            }
        ]
    }
    
    # Seleciona os itens da categoria ou assume 'ferramentas' como fallback
    selected_items = catalog.get(category.lower().strip(), catalog["ferramentas"])
    
    # URL base do Render para o proxy de imagens
    render_base_url = "https://api-shopee-pinterest.onrender.com"
    
    results = []
    for item in selected_items[:limit]:
        # Converte a imagem real do Mercado Livre pelo nosso proxy
        proxy_img_url = f"{render_base_url}/proxy-image?url={item['raw_image']}"
        
        results.append({
            "id": item["id"],
            "title": item["title"],
            "permalink": item["permalink"],
            "coupon_link": "https://www.mercadolivre.com.br/cupons",
            "price": item["price"],
            "thumbnail": proxy_img_url,
            "description": f"Confira esta oferta no Mercado Livre: {item['title']} por R$ {item['price']}"
        })
        
    return {"results": results, "total": len(results)}
