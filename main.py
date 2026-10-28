import xml.etree.ElementTree as ET

@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ofertas", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    # Endpoint RSS oficial do Mercado Livre Brasil
    rss_url = "https://lista.mercadolivre.com.br/ofertas_Rss-xml"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(rss_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {"error": f"Erro Mercado Livre: {response.status_code}", "results": []}
            
        root = ET.fromstring(response.text)
        results = []
        
        # Mapeia os itens do RSS para a mesma estrutura da API tradicional
        for item in root.findall("./channel/item")[:limit]:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            description = item.find("description").text if item.find("description") is not None else ""
            
            results.append({
                "title": title,
                "permalink": link,
                "description": description
            })
            
        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}
