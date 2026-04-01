from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from model import TranslationModel

# ── Modèles Pydantic ──────────────────────────────────────────────────────────

class TranslationRequest(BaseModel):
    text: str
    num_beams: int = 4

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"text": "Bonjour, comment allez-vous ?", "num_beams": 4}
            ]
        }
    }

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str = "Français"
    target_language: str = "Wolof"


# ── Lifespan (chargement du modèle au démarrage) ──────────────────────────────

ml_model: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏳ Chargement du modèle de traduction...")
    ml_model["translator"] = TranslationModel()
    print("✅ Modèle chargé avec succès !")
    yield
    ml_model.clear()
    print("🛑 Modèle déchargé.")


# ── Application FastAPI ───────────────────────────────────────────────────────

app = FastAPI(
    title="API Traduction Français → Wolof",
    description=(
        "API de traduction automatique du **français** vers le **wolof** "
        "basée sur un modèle MarianMT fine-tuné."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Santé"])
def root():
    """Vérifie que l'API est en ligne."""
    return {"status": "ok", "message": "API Traduction Français → Wolof opérationnelle"}


@app.get("/health", tags=["Santé"])
def health():
    """Vérifie l'état du modèle."""
    model_loaded = "translator" in ml_model
    return {
        "status": "ok" if model_loaded else "error",
        "model_loaded": model_loaded,
    }


@app.post("/translate", response_model=TranslationResponse, tags=["Traduction"])
def translate(request: TranslationRequest):

    if "translator" not in ml_model:
        raise HTTPException(status_code=503, detail="Modèle non disponible.")

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte ne peut pas être vide.")

    try:
        translation = ml_model["translator"].translate(
            text=request.text,
            num_beams=request.num_beams,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la traduction : {str(e)}")

    return TranslationResponse(
        original_text=request.text,
        translated_text=translation,
    )
