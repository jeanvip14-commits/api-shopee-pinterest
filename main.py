@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ferramentas", description="Termo da busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    search_term = q.strip() if q and q.strip() else "ferramentas"
    target_url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    if SCRAPER_API_KEY:
        # Usa HTTPS (https://) e adiciona render=false para a resposta vir muito mais rapida
        url = f"https://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=false"
    else:
        url = target_url

    headers = {"Accept": "application/json"}
    
    try:
        # Aumenta o timeout para 60 segundos para evitar Read timed out
        resp = requests.get(url, headers=headers, timeout=60)
        results = []
        
        if resp.status_code == 200:
            data = resp.json()
            raw_results = data.get("results", [])
            
            for item in raw_results:
                results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "permalink": item.get("permalink"),
                    "price": item.get("price"),
                    "thumbnail": item.get("secure_thumbnail") or item.get("thumbnail"),
                    "description": f"Confira esta oferta no Mercado Livre: {item.get('title')} por R$ {item.get('price')}"
                })
                
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}
