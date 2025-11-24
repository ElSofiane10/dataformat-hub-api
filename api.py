from fastapi import FastAPI, UploadFile, File
from fastapi.openapi.docs import get_swagger_ui_html
from converter import convert_csv_to_json
import tempfile
from pathlib import Path

# On désactive les docs automatiques et on les recrée à la main
app = FastAPI(
    title="CSV to JSON Converter API",
    docs_url=None,              # on désactive les docs intégrées
    redoc_url=None,
    openapi_url="/openapi.json" # chemin pour le schéma OpenAPI
)


@app.get("/")
async def root():
    return {"status": "ok", "message": "CSV to JSON API is running"}


# Route /docs créée manuellement
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="CSV to JSON Converter API - Docs",
    )


@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    # Sauvegarde du CSV uploadé dans un fichier temporaire
    suffix = Path(file.filename).suffix or ".csv"
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_input.write(await file.read())
    temp_input.close()

    # Conversion
    out_path = convert_csv_to_json(temp_input.name)

    # Lecture du JSON généré
    with open(out_path, "r", encoding="utf-8") as f:
        json_data = f.read()

    return {"filename": Path(out_path).name, "json": json_data}
