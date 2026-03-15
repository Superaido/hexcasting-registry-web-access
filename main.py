import json
from fastapi import FastAPI, HTTPException
from typing import Optional

app = FastAPI()

with open("hexbug_registry.json", encoding="utf-8") as f:
    DATA = json.load(f)

@app.get("/get-id")
def get_id(name: str):
    for pattern in DATA["patterns"]:
        if pattern["name"] == name:
            return pattern["id"]

@app.get("get-data/{path:path}")
def get_data(path: str):
    # Split the URL path into keys
    keys = [k for k in path.strip("/").split("/") if k]
    
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