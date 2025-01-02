# 404 Crawler

## Descripción

**404 Crawler** es una herramienta en Python diseñada para rastrear todas las subpáginas de un mismo dominio hasta una profundidad específica, identificando enlaces rotos (códigos de estado HTTP 404 y otros errores similares). El crawler:

- **Normaliza URLs** para evitar duplicados, eliminando `www.` y fragmentos (`#`).
- **Registra y guarda** todos los enlaces encontrados junto con sus códigos de estado HTTP en un archivo CSV.
- **Evita re-visitas** a páginas ya rastreadas, optimizando el proceso de rastreo.
- **Utiliza múltiples hilos** para acelerar la tarea de rastreo.
- **Soporta URLs locales** (`file://`) además de HTTP/HTTPS.

Esta herramienta es ideal para desarrolladores web y administradores de sitios que desean mantener la integridad de sus enlaces y mejorar la experiencia del usuario al eliminar enlaces rotos.

## Características

- **Profundidad Configurable**: Rastrear subpáginas hasta la profundidad que especifiques (`-d` / `--depth`).
- **Normalización de URLs**: Elimina `www.` del dominio y fragmentos (`#`), evitando duplicados.
- **Registro Completo**: Guarda tanto enlaces válidos como aquellos que retornan códigos de error (por ejemplo, 404).
- **CSV Detallado**: El archivo CSV resultante contiene dos columnas: `enlace_roto` y `codigo_estado`.
- **Concurrente**: Utiliza `ThreadPoolExecutor` para procesar múltiples URLs en paralelo, acelerando el rastreo.
- **Soporte para URLs Locales**: Además de HTTP/HTTPS, puede rastrear archivos locales usando el esquema `file://`.
- **Registro de Redirecciones**: Muestra la cadena de redirecciones (301, 302) si existen.
- **Evita Repeticiones**: No re-visita URLs ya rastreadas, optimizando el rendimiento.
- **BFS (Breadth-First Search)**: Utiliza un enfoque de búsqueda en amplitud para rastrear URLs de manera eficiente.

## Instalación

### Requisitos Previos

- **Python 3.6** o superior.
- **pip**: Administrador de paquetes de Python.

### Clonar el Repositorio


```bash
git clone https://github.com/luisterron/404_crawler.git
cd 404_crawler
