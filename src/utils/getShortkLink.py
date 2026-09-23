import requests

def getShortLink(link: str) -> str:
    """Fonction qui permet de raccourcir l'URL donné."""

    api_url = f"http://tinyurl.com/api-create.php?url={link}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text
    else:
        return None