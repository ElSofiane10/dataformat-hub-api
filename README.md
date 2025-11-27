DataFormat Hub – Multi-Format Converter API
-------------------------------------------

API simple, robuste et professionnelle pour convertir et nettoyer des données :
CSV, JSON, Excel (.xlsx), XML, HTML (tableaux) et texte brut.

Déploiement : https://dataformat-hub-api.onrender.com


MODULES INCLUS
--------------

1. CSV → JSON                (POST /csv/to-json)
2. JSON → CSV                (POST /json/to-csv)
3. CSV → Excel (.xlsx)       (POST /csv/to-excel)
4. Excel (.xlsx) → CSV       (POST /excel/to-csv)
5. JSON Formatter            (POST /json/format)
6. XML → JSON                (POST /xml/to-json)
7. JSON → XML                (POST /json/to-xml)
8. HTML Table → JSON         (POST /html-table/to-json)
9. CSV URL → JSON            (POST /csv/url-to-json)
10. Text Cleaner             (POST /text/clean)


VERIFICATION RAPIDE
-------------------

curl https://dataformat-hub-api.onrender.com/

Réponse attendue :
{
  "status": "ok",
  "message": "Multi-Format Converter API is running",
  "modules": [...]
}


EXEMPLES D’UTILISATION
----------------------

[1] CSV → JSON
curl -X POST "https://dataformat-hub-api.onrender.com/csv/to-json" \
     -F "file=@test.csv" \
     -F "delimiter=," \
     -F "encoding=utf-8" \
     -F "has_header=true" \
     -F "pretty=false"

[2] JSON Formatter
curl -X POST "https://dataformat-hub-api.onrender.com/json/format" \
     -F "file=@ugly.json" \
     -F "mode=pretty" \
     -F "validate=true"

[3] Text Cleaner
curl -X POST "https://dataformat-hub-api.onrender.com/text/clean" \
     -H "Content-Type: application/json" \
     -d "{\"text\": \"  Héllo   Wôrld \\n\"}"


LIMITES TECHNIQUES
------------------

- JSON max :               1 MB
- Lignes CSV max :         100 000
- Timeout URL → CSV :      10 secondes
- Encodage par défaut :    UTF-8
- XML sécurisé :           profondeur et nombre de nœuds limités
- En cas d’erreur :        code 400 + message explicite


TECHNOLOGIES UTILISÉES
----------------------

FastAPI, Uvicorn, Openpyxl, BeautifulSoup4, lxml, httpx, Python 3.x


LICENCE
-------

Usage libre : personnel et commercial.
© DataFormat Hub
