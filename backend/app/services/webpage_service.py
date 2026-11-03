
import httpx
from bs4 import BeautifulSoup


def extract_text_from_webpage(url: str) -> dict:
    """
    Download a webpage and extract its readable text.
    """

    headers = {
        "User-Agent": "RAGChromeExtension/1.0"
    }

    with httpx.Client(
        timeout=15.0,
        follow_redirects=True,
        headers=headers,
    ) as client:
        response = client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove content that is not useful for answering questions.
    for element in soup(
        ["script", "style", "nav", "footer", "header", "noscript"]
    ):
        element.decompose()

    title = (
        soup.title.get_text(strip=True)
        if soup.title
        else url
    )

    content = soup.get_text(separator=" ", strip=True)

    if not content:
        raise ValueError("No readable text found on this webpage.")

    return {
        "url": url,
        "title": title,
        "text": content,
    }