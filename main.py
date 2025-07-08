from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict
import asyncio
import aiohttp

app = FastAPI()

class SearchQuery(BaseModel):
    country: str
    query: str

class PriceResult(BaseModel):
    website: str
    product_name: str
    price: float
    url: str

RETAILERS = {
    "amazon": {
        "us": "https://www.amazon.com",
        "in": "https://www.amazon.in",
        "search_path": "/s?k={query}",
        "price_selector": ".a-price-whole",
        "name_selector": ".a-size-medium.a-text-normal",
        "url_selector": ".a-link-normal.s-no-outline"
    },
    "walmart": {
        "us": "https://www.walmart.com",
        "search_path": "/search?q={query}",
        "price_selector": "[data-automation-id='product-price']",
        "name_selector": "[data-automation-id='product-title']",
        "url_selector": "a[data-automation-id='product-title-link']"
    },
    "flipkart": {
        "in": "https://www.flipkart.com",
        "search_path": "/search?q={query}&sid=tyy%2C4io",
        "price_selector": ".Nx9bqj._4b5DiR",
        "name_selector": ".KzDlHZ",
        "url_selector": ".CGtC98"
    }
}

async def fetch_page(session, url, headers, retries=3):
    for attempt in range(retries):
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                print(f"Attempt {attempt+1}: Status {response.status} for {url}")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {url}: {e}")
            await asyncio.sleep(2)
    return None

def parse_price(price_str: str) -> float:
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

async def scrape_retailer(session, retailer: str, base_url: str, config: Dict, query: str) -> List[PriceResult]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
    }
    search_url = f"{base_url}{config['search_path'].format(query=query.replace(' ', '+'))}"
    html = await fetch_page(session, search_url, headers)
    
    if not html:
        print(f"Failed to fetch {search_url} for {retailer}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    price_elements = soup.select(config['price_selector'])
    name_elements = soup.select(config['name_selector'])
    url_elements = soup.select(config['url_selector'])
    
    print(f"{retailer} - Prices found: {len(price_elements)}, Names found: {len(name_elements)}, URLs found: {len(url_elements)}")
    
    for price_el, name_el, url_el in zip(price_elements[:5], name_elements[:5], url_elements[:5]):
        price = parse_price(price_el.text.strip())
        if price == 0.0:
            print(f"{retailer} - Invalid price for item: {price_el.text.strip()}")
            continue
            
        name = name_el.text.strip() if name_el else "N/A"
        url = url_el['href'] if url_el else "#"
        if not url.startswith('http'):
            url = f"{base_url}{url}"
            
        print(f"{retailer} - Found: Name={name}, Price={price}, URL={url}")
        results.append(PriceResult(
            website=retailer,
            product_name=name,
            price=price,
            url=url
        ))
    
    return results

@app.post("/search", response_model=List[PriceResult])
async def search_prices(search: SearchQuery):
    results = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for retailer, config in RETAILERS.items():
            base_url = config.get(search.country.lower(), '')
            if base_url:
                tasks.append(scrape_retailer(session, retailer, base_url, config, search.query))
        
        if not tasks:
            raise HTTPException(status_code=400, detail="No retailers available for the specified country")
            
        retailer_results = await asyncio.gather(*tasks)
        for retailer_result in retailer_results:
            results.extend(retailer_result)
    
    # Sort by price ascending
    results.sort(key=lambda x: x.price)
    
    return results

@app.get("/")
async def root():
    return {"message": "Price Comparison API"}