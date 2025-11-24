from fastapi import FastAPI, UploadFile, File
from converter import convert_csv_to_json
import tempfile
from pathlib import Path

app = FastAPI(title="CSV to JSON Converter API")

@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    # Save uploaded CSV to temp file
    suffix = Path(file.filename).suffix or ".csv"
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_input.write(await file.read())
    temp_input.close()

    # Conversion
    out_path = convert_csv_to_json(temp_input.name)

    # Read JSON output
    with open(out_path, "r", encoding="utf-8") as f:
        json_data = f.read()

    return {"filename": Path(out_path).name, "json": json_data}
