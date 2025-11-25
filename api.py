from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from pathlib import Path
import csv
import io
import json
import urllib.request
import urllib.error

app = FastAPI(
    title="CSV to JSON Converter API",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json"
)


@app.get("/")
async def root():
    return {"status": "ok", "message": "CSV to JSON API is running"}


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="CSV to JSON Converter API - Docs",
    )


def convert_csv_bytes_to_json(
    csv_bytes: bytes,
    delimiter: str = ",",
    encoding: str = "utf-8",
    has_header: bool = True,
) -> list[dict]:
    """
    Convertit des données CSV (bytes) en liste de dictionnaires JSON.
    Respecte le délimiteur, l'encodage et la présence/absence d'en-tête.
    """
    try:
        text = csv_bytes.decode(encoding)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de décoder le fichier avec l'encodage '{encoding}'.",
        )

    f = io.StringIO(text)

    try:
        if has_header:
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = [dict(row) for row in reader]
        else:
            # Pas d'en-tête : on génère des colonnes col1, col2, ...
            reader = csv.reader(f, delimiter=delimiter)
            rows = []
            for row in reader:
                cols = {f"col{i+1}": value for i, value in enumerate(row)}
                rows.append(cols)
    except csv.Error as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de la lecture du CSV : {str(e)}",
        )

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="Le fichier CSV est vide ou ne contient aucune ligne exploitable.",
        )

    return rows


@app.post("/convert")
async def convert_file(
    file: UploadFile = File(..., description="Fichier CSV à convertir en JSON."),
    delimiter: str = Query(",", description="Délimiteur utilisé dans le CSV (par défaut: ',')."),
    encoding: str = Query("utf-8", description="Encodage du fichier CSV (par défaut: 'utf-8')."),
    has_header: bool = Query(True, description="Le CSV contient-il une première ligne d'en-têtes ?"),
    pretty: bool = Query(
        False,
        description="Formater le JSON avec indentations (true) ou compact (false, par défaut).",
    ),
):
    """
    Convertit un fichier CSV uploadé en JSON.
    Retourne une liste d'objets JSON et des métadonnées.
    """
    # Vérification extension basique (pas bloquant, juste pour feedback)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ""}:
        # On ne bloque pas, mais on prévient
        warning = f"Extension '{suffix}' inhabituelle pour un CSV."
    else:
        warning = None

    # Lecture du fichier
    try:
        csv_bytes = await file.read()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Impossible de lire le fichier uploadé.",
        )

    if not csv_bytes:
        raise HTTPException(
            status_code=400,
            detail="Le fichier est vide.",
        )

    rows = convert_csv_bytes_to_json(
        csv_bytes=csv_bytes,
        delimiter=delimiter,
        encoding=encoding,
        has_header=has_header,
    )

    # Formatage du JSON
    if pretty:
        json_text = json.dumps(rows, ensure_ascii=False, indent=2)
    else:
        json_text = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

    response_payload = {
        "filename": file.filename,
        "rows_count": len(rows),
        "warning": warning,
        "data": rows,          # JSON exploitable directement
        "data_string": json_text,  # version chaîne si besoin
    }

    return JSONResponse(content=response_payload)


@app.get("/convert-url")
async def convert_from_url(
    url: str = Query(..., description="URL pointant vers un fichier CSV accessible publiquement."),
    delimiter: str = Query(",", description="Délimiteur utilisé dans le CSV (par défaut: ',')."),
    encoding: str = Query("utf-8", description="Encodage du fichier CSV (par défaut: 'utf-8')."),
    has_header: bool = Query(True, description="Le CSV contient-il une première ligne d'en-têtes ?"),
    pretty: bool = Query(
        False,
        description="Formater le JSON avec indentations (true) ou compact (false, par défaut).",
    ),
):
    """
    Récupère un CSV via une URL, le convertit en JSON et le renvoie.
    Utile pour les pipelines automatisés.
    """
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            csv_bytes = resp.read()
    except urllib.error.HTTPError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur HTTP en récupérant l'URL : {e.code} {e.reason}",
        )
    except urllib.error.URLError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible d'accéder à l'URL fournie : {e.reason}",
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Erreur inconnue lors de la récupération de l'URL.",
        )

    if not csv_bytes:
        raise HTTPException(
            status_code=400,
            detail="Le contenu récupéré depuis l'URL est vide.",
        )

    rows = convert_csv_bytes_to_json(
        csv_bytes=csv_bytes,
        delimiter=delimiter,
        encoding=encoding,
        has_header=has_header,
    )

    if pretty:
        json_text = json.dumps(rows, ensure_ascii=False, indent=2)
    else:
        json_text = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

    response_payload = {
        "source_url": url,
        "rows_count": len(rows),
        "data": rows,
        "data_string": json_text,
    }

    return JSONResponse(content=response_payload)


@app.get("/stats")
async def stats():
    """
    Endpoint simple d'info. Plus tard on pourra brancher des vraies stats.
    """
    return {
        "module": "csv_to_json",
        "version": "1.0.0-pro",
        "status": "ready",
        "endpoints": ["/convert", "/convert-url"],
    }
