from flask import Flask, request, jsonify
from flask_cors import CORS
from sumeval.metrics.rouge import RougeCalculator
from sumeval.metrics.bleu import BLEUCalculator
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def search_google(query):
    print("GOOGLE_API_KEY:", GOOGLE_API_KEY)
    print("GOOGLE_CSE_ID:", GOOGLE_CSE_ID)
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return []  # Return empty if keys aren't available
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={query}"
    response = requests.get(url)
    results = response.json().get("items", [])
    return results

def fetch_and_summarize(url):

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        content = " ".join([p.get_text() for p in paragraphs[:5]])  # Limit to the first few paragraphs for summary

        rouge = RougeCalculator(stopwords=True, lang="en")
        summary = rouge.rouge_l(
            summary=content, 
            references=content[:200]
        )
        return content[:250]
    except Exception as e:
        print(f"Error fetching or summarizing {url}: {e}")
        return None

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get("query")

    # Perform the Google search
    search_results = search_google(query)
    print("Search Results:", search_results)  # Log search results
    summaries = []
    for result in search_results:
        url = result.get("link")
        title = result.get("title")
        
        summary = fetch_and_summarize(url)
        if summary:
            summaries.append({
                "title": title,
                "url": url,
                "summary": summary
            })

    return jsonify(summaries)

if __name__ == '__main__':
    app.run(debug=True)
