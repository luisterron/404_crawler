# Frutascandil Crawler

## Descripción

**Frutascandil Crawler** es una herramienta en Python diseñada para rastrear todas las subpáginas de un mismo dominio sin límite de profundidad. El crawler:

- **Normaliza URLs** para evitar duplicados, eliminando `www.` y fragmentos (`#`).
- **Registra y guarda** todos los enlaces encontrados junto con sus códigos de estado HTTP en un archivo CSV.
- **Evita re-visitas** a páginas ya rastreadas, optimizando el proceso de rastreo.
- **Utiliza múltiples hilos** para acelerar la tarea de rastreo.
- **Soporta** URLs locales (`file://`) además de HTTP/HTTPS.

## Características

- **Profundidad Infinita**: Rastreará todas las subpáginas disponibles dentro del mismo dominio.
- **Sin Timeout**: No aplica tiempo de espera para las solicitudes HTTP, evitando cortes prematuros.
- **Registro Completo**: Guarda tanto enlaces válidos como aquellos que retornan códigos de error (por ejemplo, 404).
- **CSV Detallado**: El archivo CSV resultante contiene dos columnas: `enlace` y `codigo_estado`.
- **Concurrente**: Utiliza `ThreadPoolExecutor` para procesar múltiples URLs en paralelo.

## Instalación

1. **Clonar el Repositorio**

   ```bash
   git clone https://github.com/luisterron/404_crawler.git
   cd 404_crawler

## USO
    ```bash
    python 404_crawler.py https://dominio.com


