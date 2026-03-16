import json
import hashlib
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

BASE_DIR = Path("computercraft_accessible").resolve()

def sha256_file(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def build_node(path: Path):
    if path.is_dir():
        return {
            "type": "directory",
            "name": path.name,
            "path": str(path.relative_to(BASE_DIR)),
            "url_endpoint": f"/computercraft/getFilesystem?path={path.relative_to(BASE_DIR)}",
            "children": [build_node(p) for p in sorted(path.iterdir())]
        }

    elif path.is_file():
        return {
            "type": "file",
            "name": path.name,
            "path": str(path.relative_to(BASE_DIR)),
            "url_endpoint": f"/computercraft/getFile?path={path.relative_to(BASE_DIR)}",
            "hash": sha256_file(path),
            "size": path.stat().st_size
        }


@app.get("/computercraft/getFilesystem")
def computercraft_get_filesystem(path: str):
    requested_path = (BASE_DIR / path).resolve()

    # prevent directory traversal
    if not requested_path.is_relative_to(BASE_DIR):
        raise HTTPException(status_code=403, detail="Invalid path")

    if not requested_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    if not requested_path.is_dir():
        raise HTTPException(status_code=400, detail="Path must be a directory")

    return [build_node(requested_path)]


@app.get("/computercraft/getFile")
def computercraft_get_file(path: str):
    requested_path = (BASE_DIR / path).resolve()

    if not requested_path.is_relative_to(BASE_DIR):
        raise HTTPException(status_code=403, detail="Invalid path")

    if not requested_path.exists() or not requested_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(requested_path)

with open("hexbug_registry.json", encoding="utf-8") as f:
    DATA = json.load(f)

@app.get("/get-id")
def get_id(name: str):
    for pattern in DATA["patterns"].values():
        if pattern["name"] == name:
            return pattern["id"]
    raise HTTPException(status_code=404, detail=f"No pattern with name '{name}'")

@app.get("/get-data")
def get_data(path: str):
    # Split the URL path into keys
    keys = [k for k in path.strip(".").split(".") if k]
    
    node = DATA
    for key in keys:
        if isinstance(node, dict) and key in node:
            node = node[key]
        elif isinstance(node, list):
            # Support index-based access for arrays
            if key.isdigit():
                index = int(key)
                if index < len(node):
                    node = node[index]
                else:
                    raise HTTPException(status_code=404, detail=f"Index '{key}' out of range")
            else:
                raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        else:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    
    return node