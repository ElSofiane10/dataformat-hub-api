from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body
from fastapi.openapi.docs import get_swagger_ui_html
from pathlib import Path
import tempfile

from converter import (
    convert_csv_to_json,
    convert_json_to_csv,
    csv_to_excel,
    excel_to_csv,
    json_formatter,
    xml_to_json,
    json_to_xml,
    html_table_to_json,
    csv_url_to_json,
    clean_text,
)

app = FastAPI(
    title="Multi-Format Converter API",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)


# ---------------------------------------------------------------------------
# Root & docs
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Multi-Format Converter API is running",
        "modules": [
            "1. CSV -> JSON",
            "2. JSON -> CSV",
            "3. CSV -> Excel (.xlsx)",
            "4. Excel (.xlsx) -> CSV",
            "5. JSON Formatter (pretty/compact/validate)",
            "6. XML -> JSON",
            "7. JSON -> XML",
            "8. HTML Table -> JSON",
            "9. CSV URL -> JSON",
            "10. Text Cleaner",
        ],
    }


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Multi-Format Converter API - Docs",
    )


# ---------------------------------------------------------------------------
# 1. CSV -> JSON
# ---------------------------------------------------------------------------


@app.post("/csv/to-json", summary="Convertir un CSV en JSON")
async def csv_to_json_endpoint(
    file: UploadFile = File(..., description="Fichier CSV à convertir"),
    delimiter: str = Query(",", max_length=1, description="Séparateur CSV (1 caractère)"),
    encoding: str = Query("utf-8", description="Encodage du fichier CSV"),
    has_header: bool = Query(True, description="Le CSV contient-il une ligne d'en-tête ?"),
    pretty: bool = Query(False, description="Retourner le JSON indenté (lisible)"),
    max_rows: int = Query(
        100_000,
        ge=1,
        le=1_000_000,
        description="Nombre maximal de lignes à traiter",
    ),
):
    """
    Convertit un fichier CSV en JSON.
    """
    suffix = Path(file.filename or "").suffix or ".csv"
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_input.write(await file.read())
    temp_input.close()

    try:
        out_path, rows_count, warning, data = convert_csv_to_json(
            temp_input.name,
            delimiter=delimiter,
            encoding=encoding,
            has_header=has_header,
            pretty=pretty,
            max_rows=max_rows,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    json_text = out_path.read_text(encoding="utf-8")
    return {
        "filename": out_path.name,
        "rows_count": rows_count,
        "warning": warning,
        "data": data,
        "data_string": json_text,
    }


# ---------------------------------------------------------------------------
# 2. JSON -> CSV
# ---------------------------------------------------------------------------


@app.post("/json/to-csv", summary="Convertir un JSON en CSV")
async def json_to_csv_endpoint(
    file: UploadFile = File(..., description="Fichier JSON à convertir"),
    delimiter: str = Query(",", max_length=1, description="Séparateur CSV (1 caractère)"),
    encoding: str = Query("utf-8", description="Encodage du fichier JSON"),
    has_header: bool = Query(
        True,
        description="Écrire une ligne d'en-tête si le JSON est une liste d'objets",
    ),
    max_rows: int = Query(
        100_000,
        ge=1,
        le=1_000_000,
        description="Nombre maximal de lignes exportées",
    ),
    flatten_nested: bool = Query(
        False,
        description="Aplatir les objets/arrays imbriqués (JSON sérialisé dans une cellule)",
    ),
):
    """
    Convertit un fichier JSON (liste) en CSV.
    """
    raw_bytes = await file.read()
    try:
        json_text = raw_bytes.decode(encoding)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de décoder le fichier avec l'encodage '{encoding}'.",
        )

    try:
        out_path, rows_count, warning = convert_json_to_csv(
            json_text=json_text,
            delimiter=delimiter,
            has_header=has_header,
            max_rows=max_rows,
            flatten_nested=flatten_nested,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    csv_text = out_path.read_text(encoding="utf-8")
    return {
        "filename": out_path.name,
        "rows_count": rows_count,
        "warning": warning,
        "csv": csv_text,
    }


# ---------------------------------------------------------------------------
# 3. CSV -> Excel (.xlsx)
# ---------------------------------------------------------------------------


@app.post("/csv/to-excel", summary="Convertir un CSV en fichier Excel (.xlsx)")
async def csv_to_excel_endpoint(
    file: UploadFile = File(..., description="Fichier CSV à convertir"),
    delimiter: str = Query(",", max_length=1, description="Séparateur CSV"),
    encoding: str = Query("utf-8", description="Encodage du fichier CSV"),
    has_header: bool = Query(True, description="Le CSV contient-il une ligne d'en-tête ?"),
    sheet_name: str = Query("Sheet1", description="Nom de l'onglet Excel à créer"),
    max_rows: int = Query(
        100_000,
        ge=1,
        le=1_000_000,
        description="Nombre maximal de lignes à copier",
    ),
):
    """
    Convertit un CSV en fichier Excel (.xlsx).
    """
    suffix = Path(file.filename or "").suffix or ".csv"
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_input.write(await file.read())
    temp_input.close()

    try:
        out_path, rows_count, warning = csv_to_excel(
            temp_input.name,
            delimiter=delimiter,
            encoding=encoding,
            has_header=has_header,
            sheet_name=sheet_name,
            max_rows=max_rows,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "filename": out_path.name,
        "rows_count": rows_count,
        "warning": warning,
    }


# ---------------------------------------------------------------------------
# 4. Excel (.xlsx) -> CSV
# ---------------------------------------------------------------------------


@app.post("/excel/to-csv", summary="Convertir un fichier Excel (.xlsx) en CSV")
async def excel_to_csv_endpoint(
    file: UploadFile = File(..., description="Fichier Excel à convertir"),
    delimiter: str = Query(",", max_length=1, description="Séparateur CSV en sortie"),
    sheet_name: str | None = Query(
        None,
        description="Nom de la feuille à lire (par défaut : feuille active)",
    ),
    has_header: bool = Query(
        True,
        description="La première ligne correspond-elle à l'en-tête ?",
    ),
    max_rows: int = Query(
        100_000,
        ge=1,
        le=1_000_000,
        description="Nombre maximal de lignes à exporter",
    ),
):
    """
    Convertit un fichier Excel (.xlsx) en CSV.
    """
    suffix = Path(file.filename or "").suffix or ".xlsx"
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_input.write(await file.read())
    temp_input.close()

    try:
        out_path, rows_count, warning = excel_to_csv(
            temp_input.name,
            delimiter=delimiter,
            sheet_name=sheet_name,
            has_header=has_header,
            max_rows=max_rows,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    csv_text = out_path.read_text(encoding="utf-8")
    return {
        "filename": out_path.name,
        "rows_count": rows_count,
        "warning": warning,
        "csv": csv_text,
    }


# ---------------------------------------------------------------------------
# 5. JSON Formatter (pretty / compact / validate)
# ---------------------------------------------------------------------------


@app.post("/json/format", summary="Formater et valider un JSON")
async def json_format_endpoint(
    file: UploadFile = File(..., description="Fichier JSON à formater"),
    encoding: str = Query("utf-8", description="Encodage du fichier JSON"),
    mode: str = Query(
        "pretty",
        regex="^(pretty|compact)$",
        description="Mode de sortie : 'pretty' ou 'compact'",
    ),
    indent: int = Query(2, ge=0, le=8, description="Indentation pour le mode 'pretty'"),
    sort_keys: bool = Query(False, description="Trier les clés alphabétiquement"),
    ensure_ascii: bool = Query(
        False,
        description="Échapper les caractères non-ASCII",
    ),
    validate: bool = Query(
        True,
        description="Tenter de valider le JSON et retourner l'erreur le cas échéant",
    ),
    max_size_kb: int = Query(
        1024,
        ge=1,
        le=10_000,
        description="Taille maximale du JSON pour éviter les abus",
    ),
):
    """
    Formate un JSON (pretty ou compact) et optionnellement le valide.
    """
    raw_bytes = await file.read()
    try:
        json_text = raw_bytes.decode(encoding)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de décoder le fichier avec l'encodage '{encoding}'.",
        )

    try:
        result = json_formatter(
            json_text,
            mode=mode,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
            validate=validate,
            max_size_kb=max_size_kb,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


# ---------------------------------------------------------------------------
# 6. XML -> JSON
# ---------------------------------------------------------------------------


@app.post("/xml/to-json", summary="Convertir un XML en JSON")
async def xml_to_json_endpoint(
    file: UploadFile = File(..., description="Fichier XML à convertir"),
    encoding: str = Query("utf-8", description="Encodage du fichier XML"),
    strip_whitespace: bool = Query(
        True,
        description="Supprimer les espaces superflus dans les textes",
    ),
    max_depth: int = Query(
        10,
        ge=1,
        le=50,
        description="Profondeur maximale de conversion",
    ),
    max_nodes: int = Query(
        10_000,
        ge=10,
        le=1_000_000,
        description="Nombre maximal de noeuds XML à analyser",
    ),
    text_key: str = Query(
        "#text",
        description="Clé utilisée pour stocker le texte d'un noeud",
    ),
):
    """
    Convertit un fichier XML en structure JSON.
    """
    raw_bytes = await file.read()
    try:
        xml_text = raw_bytes.decode(encoding)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de décoder le fichier avec l'encodage '{encoding}'.",
        )

    try:
        result = xml_to_json(
            xml_text,
            strip_whitespace=strip_whitespace,
            max_depth=max_depth,
            max_nodes=max_nodes,
            text_key=text_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


# ---------------------------------------------------------------------------
# 7. JSON -> XML
# ---------------------------------------------------------------------------


@app.post("/json/to-xml", summary="Convertir un JSON en XML")
async def json_to_xml_endpoint(
    file: UploadFile = File(..., description="Fichier JSON à convertir"),
    encoding: str = Query("utf-8", description="Encodage du fichier JSON"),
    root_tag: str = Query("root", description="Nom de la balise racine XML"),
    attr_prefix: str = Query(
        "@",
        description="Préfixe indiquant les attributs dans le JSON (ex: '@id')",
    ),
    text_key: str = Query(
        "#text",
        description="Clé pour le texte dans le JSON (ex: '#text')",
    ),
    pretty: bool = Query(True, description="Retourner un XML indenté (lisible)"),
):
    """
    Convertit un JSON en XML.
    """
    raw_bytes = await file.read()
    try:
        json_text = raw_bytes.decode(encoding)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de décoder le fichier avec l'encodage '{encoding}'.",
        )

    try:
        xml_str = json_to_xml(
            json_text,
            root_tag=root_tag,
            attr_prefix=attr_prefix,
            text_key=text_key,
            pretty=pretty,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"xml": xml_str}


# ---------------------------------------------------------------------------
# 8. HTML Table -> JSON
# ---------------------------------------------------------------------------


@app.post("/html-table/to-json", summary="Convertir un tableau HTML en JSON")
async def html_table_to_json_endpoint(
    file: UploadFile = File(..., description="Fichier HTML contenant au moins un tableau"),
    encoding: str = Query("utf-8", description="Encodage du fichier HTML"),
    table_index: int = Query(
        0,
        ge=0,
        description="Index du tableau à extraire (0 = premier tableau)",
    ),
    has_header: bool = Query(
        True,
        description="Première ligne = en-tête de colonnes ?",
    ),
    convert_numbers: bool = Query(
        True,
        description="Essayer de convertir les nombres (ex: '3,14' -> 3.14)",
    ),
    max_rows: int = Query(
        10_000,
        ge=1,
        le=100_000,
        description="Nombre maximal de lignes à extraire",
    ),
):
    """
    Extrait un tableau HTML et le convertit en JSON.
    """
    raw_bytes = await file.read()
    try:
        html_text = raw_bytes.decode(encoding)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de décoder le fichier avec l'encodage '{encoding}'.",
        )

    try:
        data = html_table_to_json(
            html_text,
            table_index=table_index,
            has_header=has_header,
            convert_numbers=convert_numbers,
            max_rows=max_rows,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"rows": data, "rows_count": len(data)}


# ---------------------------------------------------------------------------
# 9. CSV URL Fetcher (CSV URL -> JSON)
# ---------------------------------------------------------------------------


@app.post("/csv/url-to-json", summary="Télécharger un CSV depuis une URL et le convertir en JSON")
async def csv_url_to_json_endpoint(
    url: str = Query(..., description="URL directe du fichier CSV"),
    delimiter: str = Query(",", max_length=1, description="Séparateur CSV"),
    encoding: str = Query("utf-8", description="Encodage supposé du CSV"),
    has_header: bool = Query(True, description="Le CSV contient-il une ligne d'en-tête ?"),
    pretty: bool = Query(False, description="Retourner le JSON indenté"),
    max_rows: int = Query(
        100_000,
        ge=1,
        le=1_000_000,
        description="Nombre maximal de lignes à traiter",
    ),
    timeout: float = Query(
        10.0,
        ge=1.0,
        le=60.0,
        description="Timeout HTTP en secondes pour la requête",
    ),
):
    """
    Télécharge un CSV depuis une URL HTTP/HTTPS, puis le convertit en JSON.
    """
    try:
        out_path, rows_count, warning, data = csv_url_to_json(
            url,
            delimiter=delimiter,
            encoding=encoding,
            has_header=has_header,
            pretty=pretty,
            max_rows=max_rows,
            timeout=timeout,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    json_text = out_path.read_text(encoding="utf-8")
    return {
        "filename": out_path.name,
        "rows_count": rows_count,
        "warning": warning,
        "data": data,
        "data_string": json_text,
    }


# ---------------------------------------------------------------------------
# 10. Text Cleaner
# ---------------------------------------------------------------------------


@app.post("/text/clean", summary="Nettoyer un texte (trim, accents, unicode, espaces...)")
async def text_clean_endpoint(
    payload: dict = Body(
        ...,
        example={"text": "  Héllo   Wörld   \n"},
        description="Objet JSON contenant la clé 'text'",
    ),
    trim: bool = Query(True, description="Supprimer les espaces en début/fin"),
    normalize_unicode: bool = Query(
        True,
        description="Normaliser Unicode (NFC)",
    ),
    remove_accents: bool = Query(
        False,
        description="Supprimer les accents (é -> e, ö -> o...)",
    ),
    collapse_whitespace: bool = Query(
        True,
        description="Compresser les espaces multiples en un seul",
    ),
    to_lower: bool = Query(False, description="Convertir en minuscules"),
    max_length: int = Query(
        10_000,
        ge=1,
        le=1_000_000,
        description="Longueur maximale acceptée du texte",
    ),
):
    """
    Nettoie un texte brut selon plusieurs options.
    """
    if "text" not in payload or not isinstance(payload["text"], str):
        raise HTTPException(status_code=400, detail="Le champ 'text' est requis et doit être une chaîne.")

    try:
        result = clean_text(
            payload["text"],
            trim=trim,
            normalize_unicode=normalize_unicode,
            remove_accents=remove_accents,
            collapse_whitespace=collapse_whitespace,
            to_lower=to_lower,
            max_length=max_length,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result
