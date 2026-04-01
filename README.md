# 🌍 Traducteur Français → Wolof

Système de traduction automatique neuronale du **français** vers le **wolof**, basé sur un modèle **MarianMT fine-tuné**, exposé via une **API FastAPI** et une **interface Streamlit**.

---

## 📁 Structure du projet

```
.
├── model.py        # Classe TranslationModel (chargement & inférence)
├── api.py         # API REST FastAPI
├── app.py          # Interface utilisateur Streamlit
├── finetuned_fr_wolof/   # Répertoire du modèle fine-tuné (MarianMT)
├── traduction-fr-to-wolof.ipynb   # notebook d'entrainement
├── requirements.txt   # Liste des dépendances
├── evaluation_metrics.json # resulatats de l'evaluation
├── evaluation_resuls.csv # datasets avec les resultats de l'evaluation
├── eval.py # scirpt d'evaluation

└── README.md
```

---

## ⚙️ Prérequis

- Python **3.9+**
- GPU CUDA (optionnel, mais recommandé pour de meilleures performances)
- Le dossier `finetuned_fr_wolof/` contenant le modèle fine-tuné

### Installation des dépendances

```bash
pip install -r requirements.txt
```

---

## 🧠 Modèle (`model.py`)

La classe `TranslationModel` encapsule le chargement et l'inférence du modèle MarianMT.


### Paramètres
```
| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `text` | `str` | — | Texte source en français |
| `num_beams` | `int` | `4` | Nombre de faisceaux (beam search) — plus élevé = meilleure qualité, plus lent |
```
### Comportement

- Détecte automatiquement le **GPU** (CUDA) ou repasse sur le **CPU**
- Charge le modèle et le tokenizer depuis `finetuned_fr_wolof/`
- Utilise `torch.no_grad()` pour l'inférence (optimisation mémoire)
- Longueur maximale de sortie : **128 tokens**

---

## 🚀 API FastAPI (`api.py`)

### Lancer le serveur

```bash
uvicorn api:app --reload
```

Le serveur démarre sur `http://127.0.0.1:8000`.

> Le modèle est chargé **une seule fois** au démarrage via le mécanisme `lifespan` de FastAPI.

### Endpoints
```
| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/` | Vérifie que l'API est en ligne |
| `GET` | `/health` | Vérifie l'état de chargement du modèle |
| `POST` | `/translate` | Traduit un texte français → wolof |
```
### `POST /translate`

**Corps de la requête :**
```json
{
  "text": "Bonjour, comment allez-vous ?",
  "num_beams": 4
}
```

**Réponse :**
```json
{
  "original_text": "Bonjour, comment allez-vous ?",
  "translated_text": "...",
  "source_language": "Français",
  "target_language": "Wolof"
}
```

**Exemple avec `curl` :**
```bash
curl -X POST "http://127.0.0.1:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Bonjour, comment allez-vous ?", "num_beams": 4}'
```

**Exemple avec Python :**
```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/translate",
    json={"text": "Je vais bien, merci.", "num_beams": 4}
)
print(response.json()["translated_text"])
```

### Documentation interactive

Une fois le serveur lancé, la documentation Swagger est disponible à :
- **Swagger UI** → `http://127.0.0.1:8000/docs`
- **ReDoc** → `http://127.0.0.1:8000/redoc`

---

## 🖥️ Interface Streamlit (`app.py`)

### Lancer l'interface

> ⚠️ L'API FastAPI doit être lancée **avant** l'interface Streamlit.

```bash
# Terminal 1 — API
uvicorn api:app --reload

# Terminal 2 — Interface
streamlit run app.py
```

L'interface s'ouvre sur `http://localhost:8501`.

### Fonctionnalités

- 🟢 Indicateur de statut en temps réel (API connectée / hors ligne)
- 📊 Métriques de session (nombre de traductions, caractères traités)
- ✍️ Zone de saisie avec contrôle du paramètre `num_beams`
- ⚡ Affichage du résultat avec temps de réponse
- 📜 Historique des 10 dernières traductions

---

## 🔧 Options de déploiement

### Changer le port de l'API

```bash
uvicorn api:app --host 0.0.0.0 --port 8080
```

Puis mettre à jour la variable `API_URL` dans `app.py` :
```python
API_URL = "http://127.0.0.1:8080"
```

### Déploiement en production

```bash
# Avec plusieurs workers (CPU uniquement)
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```


---

## 🐛 Dépannage

| Problème | Cause probable | Solution |
|----------|---------------|----------|
| `ConnectionError` dans Streamlit | API non démarrée | Lancer `uvicorn main:app --reload` |
| `model_loaded: false` | Dossier modèle introuvable | Vérifier le chemin `finetuned_fr_wolof/` |
| Traduction lente | CPU utilisé à la place du GPU | Installer PyTorch avec support CUDA |
| `OSError: finetuned_fr_wolof` | Modèle absent | Placer le dossier du modèle à la racine du projet |

---

## 📦 Dépendances

requirements.txt