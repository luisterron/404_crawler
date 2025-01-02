#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Crawler que rastrea todas las subpáginas de un mismo dominio sin límite de profundidad.
- No aplica timeout (para evitar que cortes prematuramente).
- Filtra subpáginas al mismo dominio, ignorando 'www.' y fragmentos (#).
- Registra y guarda enlaces rotos (>= 400) en un CSV con el nombre: dominio.csv
- Evita re-visitar URLs ya exploradas.
- Puede leer archivos locales (file://), aunque suele usarse para http/https.

Uso:
    python crawler_infinito.py https://ejemplo.com --workers 20 --same_domain True
"""

import logging
import csv
import time
import sys
import requests
import urllib.parse
from queue import Queue
from urllib.parse import (
    urlparse, urljoin, urlunparse, ParseResult
)
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

def canonicalize_url(url: str) -> str:
    """
    Elimina 'www.', el fragment (#), y normaliza la URL para evitar duplicados.
    Ejemplo:
      https://www.ejemplo.com/sobre-nosotros/#section 
        => https://ejemplo.com/sobre-nosotros
    """
    parsed = urlparse(url)
    
    # Quitar 'www.' del netloc
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    
    # Eliminar fragmento (#...)
    new_fragment = ""
    
    # Reconstruir la URL sin fragment
    new_parsed = ParseResult(
        scheme=parsed.scheme,
        netloc=netloc,
        path=parsed.path,
        params=parsed.params,
        query=parsed.query,
        fragment=new_fragment
    )
    canon = urlunparse(new_parsed)
    
    # Quitar barra final si existe
    return canon.rstrip("/")

class Crawler:
    """
    Crawler que rastrea (sin límite de profundidad) todas las subpáginas del
    mismo dominio, normalizando URLs y registrando enlaces rotos.
    """

    def __init__(
        self,
        start_url: str,
        same_domain: bool = True,
        max_workers: int = 10
    ):
        """
        Parámetros principales:
        -----------------------
        - start_url: URL inicial (http/https o file://...).
        - same_domain: Solo seguir enlaces del mismo dominio (ignorando 'www.').
        - max_workers: Nº de hilos para procesar en paralelo.
        """
        # Normaliza la URL inicial
        self.start_url = canonicalize_url(start_url)
        self.same_domain = same_domain
        self.max_workers = max_workers

        # Determina el dominio base (sin 'www.')
        parsed = urlparse(self.start_url)
        self.base_domain = parsed.netloc  # ej.: ejemplo.com

        # El CSV tendrá el nombre del dominio base
        self.csv_output = f"{self.base_domain}.csv"

        # Estructuras de datos
        self.visited = set()
        self.queue = Queue()
        self.queue.put(self.start_url)  # Encolamos la URL inicial
        self.broken_links = []

        # Configura logs
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("crawler.log", "a", encoding="utf-8")
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _is_same_domain(self, url: str) -> bool:
        """
        Devuelve True si la URL dada pertenece al mismo dominio base.
        """
        canon = canonicalize_url(url)
        parsed = urlparse(canon)
        return parsed.netloc == self.base_domain

    def _parse_links(self, html_text: str, current_url: str) -> list:
        """
        Extrae y normaliza todas las URLs encontradas en <a href="...">.
        """
        soup = BeautifulSoup(html_text, "html.parser")
        found_links = []
        
        for tag in soup.find_all("a"):
            href = tag.get("href")
            if href:
                abs_url = urljoin(current_url, href.strip())
                canon = canonicalize_url(abs_url)
                found_links.append(canon)
        return found_links

    def _visit_url(self, url: str):
        """
        Visita la URL (file:// o HTTP/HTTPS), registra el código HTTP,
        parsea enlaces si es HTML y encola nuevos links si cumplen el filtro de dominio.
        No aplica límite de profundidad.
        """
        parsed = urlparse(url)

        # --- Caso file:// ---
        if parsed.scheme == "file":
            try:
                path_local = parsed.path.lstrip("/")
                with open(path_local, "r", encoding="utf-8") as f:
                    html_text = f.read()
                status_code = 200
                content_type = "text/html"
                self.logger.info(f"[LOCAL] {url} => 200 OK")
            except Exception as e:
                self.logger.error(f"[LOCAL] Error abriendo {url}: {e}")
                return

        else:
            # --- Caso HTTP/HTTPS ---
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/98.0.4758.102 Safari/537.36"
                )
            }
            try:
                # Sin timeout => timeout=None
                resp = requests.get(url, headers=headers, timeout=None, allow_redirects=True)
                status_code = resp.status_code
                content_type = resp.headers.get("Content-Type", "")
                html_text = resp.text
                
                # Mostrar posible cadena de redirecciones
                if resp.history:
                    chain_info = " -> ".join(
                        f"[{r.status_code}]{r.url}" for r in resp.history
                    ) + f" -> [{status_code}]{resp.url}"
                else:
                    chain_info = f"{url} => [{status_code}] (sin redirecciones)"

                self.logger.info(f"[HTTP] {chain_info}, {len(html_text)} bytes")

            except requests.exceptions.RequestException as e:
                self.logger.error(f"[HTTP] Excepción con {url}: {e}")
                return

        # --- Análisis del status code ---
        if status_code >= 400:
            self.logger.warning(f"[{status_code}] {url}")
            self.broken_links.append(url)
            return

        # --- Si es HTML, parsear subenlaces ---
        if "text/html" in content_type.lower():
            sublinks = self._parse_links(html_text, url)
            self.logger.info(f"Se encontraron {len(sublinks)} enlaces en {url}")

            for link in sublinks:
                # Filtrar dominio si same_domain==True
                if self.same_domain and not self._is_same_domain(link):
                    continue

                # Evitar re-visitas
                if link not in self.visited:
                    self.queue.put(link)

    def run(self):
        """
        Ejecuta el crawler, procesando hasta que no queden URLs nuevas en la cola.
        """
        self.logger.info("========== INICIANDO RASTREO ==========")
        inicio = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                futures = []

                # Vaciar la cola actual en un lote de URLs a procesar
                while not self.queue.empty():
                    current_url = self.queue.get()

                    # ¿Ya visitamos esta URL?
                    if current_url in self.visited:
                        continue

                    # Marcar como visitada
                    self.visited.add(current_url)

                    # Enviar la tarea al thread pool
                    f = executor.submit(self._visit_url, current_url)
                    futures.append(f)

                # Si no hubo nada que procesar, salimos del bucle
                if not futures:
                    break

                # Esperar a que terminen todas las tareas en este lote
                for _ in as_completed(futures):
                    pass

        tiempo_total = time.time() - inicio
        self.logger.info(f"Rastreo completado en {tiempo_total:.2f} seg.")
        self.logger.info(f"Total de URLs visitadas: {len(self.visited)}")

        # Guardar enlaces rotos si los hay
        if self.broken_links:
            self._save_csv()
            self.logger.info(f"Se encontraron {len(self.broken_links)} enlaces rotos.")
            self.logger.info(f"Guardado en {self.csv_output}")
        else:
            self.logger.info("No se encontraron enlaces rotos (>= 400).")

    def _save_csv(self):
        """
        Guarda en CSV la lista de enlaces rotos.
        El CSV se nombra como "<dominio>.csv".
        """
        try:
            with open(self.csv_output, "w", newline="", encoding="utf-8") as cfile:
                wr = csv.writer(cfile)
                wr.writerow(["enlace_roto"])
                for link in self.broken_links:
                    wr.writerow([link])
        except Exception as e:
            self.logger.error(f"No se pudo guardar {self.csv_output}: {e}")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Crawler infinito para subpáginas de un mismo dominio."
    )
    parser.add_argument(
        "start_url",
        help="URL inicial (http/https o file://...). Se normaliza para quitar 'www.'."
    )
    parser.add_argument(
        "-s", "--same_domain",
        type=bool,
        default=True,
        help="Filtrar para rastrear solo el mismo dominio (True/False)."
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=10,
        help="Número de hilos concurrentes."
    )
    args = parser.parse_args()

    crawler = Crawler(
        start_url=args.start_url,
        same_domain=args.same_domain,
        max_workers=args.workers
    )
    crawler.run()

if __name__ == "__main__":
    main()
