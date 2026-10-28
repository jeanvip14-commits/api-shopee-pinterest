@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ofertas", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    search_term = q.strip() if q and q.strip() else "ofertas"
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.mercadolivre.com.br/",
        "Origin": "https://www.mercadolivre.com.br"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=15)
        data = response.json()
        
        # Se for bloqueado (403) ou nao trouxer 'results', recorre ao endpoint de destaques por categoria
        if response.status_code != 200 or "results" not in data or not data["results"]:
            cat_url = f"https://api.mercadolibre.com/sites/MLB/search?category=MLB1051&limit={limit}"
            cat_response = session.get(cat_url, headers=headers, timeout=15)
            data = cat_response.json()
            
        return data
    except Exception as e:
        return {"error": str(e), "results": []}
