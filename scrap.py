import requests
from bs4 import BeautifulSoup

# Function to search for specific keywords in a given URL
def search_keywords_in_url(url, keywords):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        
        results = {keyword: keyword.lower() in text for keyword in keywords}
        return results
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return {keyword: False for keyword in keywords}

# List of company URLs
company_urls = [
    "https://www.puragroup.com/",
    "https://www.utacgroup.com/",
    "https://www.pcba.co.id/",
    "https://www.anugrah-elektronik.com/",
    "https://www.buenotech.co.id/",
    "https://afmlab.material.ugm.ac.id/",
    "https://www.gigasolusi.com/"
]

# Keywords to search for
keywords = ["ozone water generator", "hydrogen water generator"]

# Search for keywords in each company's website
results = {url: search_keywords_in_url(url, keywords) for url in company_urls}

# Print the results
for url, result in results.items():
    print(f"\nResults for {url}:")
    for keyword, found in result.items():
        print(f"  {keyword}: {'Found' if found else 'Not Found'}")
