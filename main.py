@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ofertas", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    search_term = q.strip() if q and q.strip() else "ofertas"
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Cache-Control": "no-cache"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=15)
        data = response.json()
        
        # Se a pesquisa direta não devolver a chave 'results', consulta por categoria geral
        if response.status_code != 200 or "results" not in data or not data["results"]:
            cat_url = f"https://api.mercadolibre.com/sites/MLB/search?category=MLB1051&limit={limit}"
            cat_response = session.get(cat_url, headers=headers, timeout=15)
            data = cat_response.json()
            
        results = []
        for item in data.get("results", [])[:limit]:
            results.append({
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "price": item.get("price", 0),
                "permalink": item.get("permalink", ""),
                "thumbnail": item.get("thumbnail", "")
            })
            
        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}
