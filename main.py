@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ofertas", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    search_term = q.strip() if q and q.strip() else "ofertas"
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        # Se nao encontrar resultados ou houver erro na busca por palavra, usa a categoria de ofertas
        if "results" not in data or not data["results"]:
            cat_url = f"https://api.mercadolibre.com/sites/MLB/search?category=MLB1051&limit={limit}"
            fallback_resp = requests.get(cat_url, headers=headers, timeout=15)
            data = fallback_resp.json()
            
        return data
    except Exception as e:
        return {"error": str(e), "results": []}
