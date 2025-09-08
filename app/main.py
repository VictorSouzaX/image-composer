from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import List
from PIL import Image
import io
import base64
import os

ASSETS_FOLDER = os.path.join(os.path.dirname(__file__), 'assets')

app = FastAPI()

class OverlayImage(BaseModel):
    image: str  # nome sem extensão
    x: int
    y: int

class ImageComposeRequest(BaseModel):
    imagens: List[OverlayImage]
    image_b64: str

@app.post("/compose")
def compose_images(data: ImageComposeRequest):
    # Decode the base64 to bytes and open as Pillow Image
    try:
        base_img_data = base64.b64decode(data.image_b64)
        base_img = Image.open(io.BytesIO(base_img_data)).convert("RGBA")
    except Exception as e:
        return {"error": "Falha ao decodificar imagem base", "details": str(e)}
    
    # Sobrepõe as imagens
    for overlay in data.imagens:
        overlay_path = os.path.join(ASSETS_FOLDER, overlay.image + ".png")
        if os.path.exists(overlay_path):
            try:
                with Image.open(overlay_path).convert("RGBA") as ov_img:
                    base_img.alpha_composite(ov_img, dest=(overlay.x, overlay.y))
            except Exception as e:
                # Não para o processo se algum overlay falhar
                continue

    # Salva o resultado em base64
    buf = io.BytesIO()
    base_img.save(buf, format="PNG")
    result_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    width, height = base_img.size

    return {
        "image_b64": result_b64,
        "width": width,
        "height": height,
    }
