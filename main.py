@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ofertas", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    # Se o parâmetro q vier vazio ou com termo muito específico, garante 'ofertas'
    search_term = q if q and len(q.strip()) > 0 else "ofertas"
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        # Garante que 'results' sempre retorne uma lista, evitando quebrar o Iterator
        if "results" not in data or not data["results"]:
            # Fallback automático caso a busca específica venha vazia
            fallback_url = f"https://api.mercadolibre.com/sites/MLB/search?q=promo&limit={limit}"
            fallback_resp = requests.get(fallback_url, headers=headers, timeout=15)
            data = fallback_resp.json()
            
        return data
    except Exception as e:
        return {"error": str(e), "results": []}
