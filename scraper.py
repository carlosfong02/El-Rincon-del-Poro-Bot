# scraper.py

import requests
from bs4 import BeautifulSoup

# La URL principal que siempre revisaremos
PATCH_LIST_URL = "https://www.leagueoflegends.com/es-mx/news/tags/patch-notes/"

def get_latest_patch_info():
    """
    Va a la página de notas de parche de LoL, encuentra el artículo más reciente y devuelve su título y URL.
    """
    try:
        # Hacemos la petición para descargar el contenido de la página
        response = requests.get(PATCH_LIST_URL)
        response.raise_for_status()  # Esto generará un error si la página no se pudo descargar

        # Usamos BeautifulSoup para "leer" el HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscamos el enlace del artículo más reciente.
        # Por lo general, es el primer enlace que sigue un patrón específico.
        # Vamos a buscar el primer enlace '<a>' que contenga '/news/game-updates/patch-' en su href.
        latest_article_link = soup.find('a', href=lambda href: href and '/news/game-updates/patch-' in href)

        if latest_article_link:
            # Extraemos el título del texto dentro del enlace o de una etiqueta de título dentro de él
            patch_title = latest_article_link.find('h2') # Asumimos que el título está en una etiqueta h2
            if not patch_title:
                patch_title = latest_article_link.text.strip() # Si no, tomamos el texto del enlace
            else:
                patch_title = patch_title.text.strip()

            # Extraemos la URL parcial (href) y la completamos
            patch_url_partial = latest_article_link['href']
            patch_url_full = "https://www.leagueoflegends.com" + patch_url_partial

            return patch_title, patch_url_full
        else:
            print("No se encontró ningún enlace de notas de parche.")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la página: {e}")
        return None, None

# --- Bloque principal para probar el scraper ---
if __name__ == "__main__":
    print("Buscando el último parche de League of Legends...")
    title, url = get_latest_patch_info()

    if title and url:
        print("\n¡Parche encontrado!")
        print(f"  Título: {title}")
        print(f"  URL: {url}")