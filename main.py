@app.get("/mercadolivre")
def get_mercadolivre_offers(
    limit: int = Query(50, description="Quantidade de produtos")
):
    token = get_meli_access_token()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    results = []
    
    # Busca itens diretamente da categoria principal MLB1051 (Ferramentas/Casa)
    url = f"https://api.mercadolibre.com/sites/MLB/search?category=MLB1051&sort=price_asc&limit={limit}"
    
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            raw_results = data.get("results", [])
            
            for item in raw_results:
                results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "permalink": item.get("permalink"),
                    "price": item.get("price"),
                    "thumbnail": item.get("thumbnail"),
                    "description": f"Confira a oferta: {item.get('title')} por R$ {item.get('price')}"
                })
                
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}
