from fastapi import FastAPI
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
    
    bx, by = base_img.size

    # Sobrepõe as imagens
    for overlay in data.imagens:
        overlay_path = os.path.join(ASSETS_FOLDER, overlay.image + ".png")
        if os.path.exists(overlay_path):
            try:
                with Image.open(overlay_path) as ov_img:
                    ov_img = ov_img.convert('RGBA')
                    ow, oh = ov_img.size
                    x, y = overlay.x, overlay.y

                    # Define área disponível para o overlay
                    avail_w = bx - x
                    avail_h = by - y

                    if avail_w <= 0 or avail_h <= 0:
                        # Overlay completamente fora da base
                        continue

                    # Se não cabe, reduz proporcionalmente
                    scale = min(1.0, avail_w / ow, avail_h / oh)
                    if scale < 1.0:
                        new_w = max(1, int(ow * scale))
                        new_h = max(1, int(oh * scale))
                        # Pillow 10 ou 9+
                        if hasattr(Image, "Resampling"):  # Pillow >= 9
                            resample = Image.Resampling.LANCZOS
                        else:
                            resample = Image.LANCZOS
                        ov_img = ov_img.resize((new_w, new_h), resample)

                    base_img.alpha_composite(ov_img, dest=(x, y))
            except Exception as e:
                print(f"Falha ao aplicar {overlay.image}: {e}")
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
