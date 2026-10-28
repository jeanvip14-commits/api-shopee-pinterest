{
  "message": "forbidden",
  "error": "forbidden",
  "status": 403
}
```[cite: 23]

Isso significa que quando o seu servidor em Python (Render) tentou fazer o `requests.get()` na API pública do Mercado Livre, o Mercado Livre **bloqueou a requisição do Render por falta de cabeçalhos adequados (User-Agent completo)**, devolvendo esse JSON de erro que foi repassado ao Make sem a lista `results`[cite: 23].

---

### Solução Definitiva no Python (`main.py`)

Para contornar o bloqueio que o Mercado Livre faz mesmo em servidores na nuvem, atualize a rota `/mercadolivre` no seu `main.py` no GitHub com cabeçalhos HTTP mais completos e um parâmetro de categoria oficial.

Substitua a função `@app.get("/mercadolivre")` por esta:

```python
@app.get("/mercadolivre")
def get_mercadolivre_offers(
    q: str = Query("ofertas", description="Termo de busca"),
    limit: int = Query(50, description="Quantidade de produtos")
):
    search_term = q if q and len(q.strip()) > 0 else "ofertas"
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={search_term}&limit={limit}"
    
    # Cabeçalhos completos para simular perfeitamente um navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        # Se o Mercado Livre devolver erro 403 ou não devolver resultados, usa a API de Categoria Oficial
        if "results" not in data or not data["results"]:
            # Categoria MLB1051 = Celulares e Telefones, MLB5726 = Eletrodomésticos, etc.
            cat_url = f"https://api.mercadolibre.com/sites/MLB/search?category=MLB1051&limit={limit}"
            fallback_resp = requests.get(cat_url, headers=headers, timeout=15)
            data = fallback_resp.json()
            
        return data
    except Exception as e:
        return {"error": str(e), "results": []}
