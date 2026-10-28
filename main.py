import feedparser

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
            
        # O feedparser tolera entidades XML inválidas e corrige o texto automaticamente
        feed = feedparser.parse(response.content)
        results = []
        
        for entry in feed.entries[:limit]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            description = entry.get("summary", "").strip()
            
            results.append({
                "title": title,
                "permalink": link,
                "description": description
            })
            
        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}
