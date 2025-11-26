# DataFormat Hub – Multi-Format Converter API

API de conversion et de nettoyage de données multi-formats : CSV, JSON, Excel, XML, HTML et texte brut.

Déployée sur : **https://dataformat-hub-api.onrender.com**

---

## 🔟 Modules inclus

1. **CSV → JSON** (`POST /csv/to-json`)  
   Convertit un fichier CSV en JSON (liste d’objets).

2. **JSON → CSV** (`POST /json/to-csv`)  
   Convertit une liste JSON en CSV (avec ou sans en-tête).

3. **CSV → Excel (.xlsx)** (`POST /csv/to-excel`)  
   Convertit un CSV en fichier Excel (.xlsx).

4. **Excel (.xlsx) → CSV** (`POST /excel/to-csv`)  
   Convertit un fichier Excel (.xlsx) en CSV.

5. **JSON Formatter (pretty / compact / validate)** (`POST /json/format`)  
   Formate un JSON (indenté ou compact) et vérifie sa validité.

6. **XML → JSON** (`POST /xml/to-json`)  
   Convertit du XML en structure JSON.

7. **JSON → XML** (`POST /json/to-xml`)  
   Convertit un JSON (dict / liste) en XML.

8. **HTML Table → JSON** (`POST /html-table/to-json`)  
   Extrait un tableau `<table>` HTML et le convertit en JSON.

9. **CSV URL → JSON** (`POST /csv/url-to-json`)  
   Télécharge un CSV depuis une URL HTTP/HTTPS et le convertit en JSON.

10. **Text Cleaner** (`POST /text/clean`)  
   Nettoie un texte (trim, accents, unicode, espaces, minuscules, etc.).

---

## 🚀 Utilisation rapide

### 1. Endpoint de santé

```bash
curl https://dataformat-hub-api.onrender.com/
