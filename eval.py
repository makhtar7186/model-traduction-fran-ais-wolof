"""
╔══════════════════════════════════════════════════════════════════╗
║        ÉVALUATION — Modèle de Traduction Français → Wolof        ║
╚══════════════════════════════════════════════════════════════════╝

Usage :
    python evaluate_fr_wolof.py --model_path ./finetuned_fr_wolof
    python evaluate_fr_wolof.py --model_path ./finetuned_fr_wolof --num_beams 5 --output_csv resultats.csv
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import evaluate
from datasets import load_dataset, DatasetDict
from transformers import MarianMTModel, MarianTokenizer
from tqdm import tqdm


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_args():
    parser = argparse.ArgumentParser(description="Évaluation du modèle FR→Wolof")
    parser.add_argument("--model_path",  type=str, default="./finetuned_fr_wolof",
                        help="Chemin vers le modèle fine-tuné")
    parser.add_argument("--dataset",     type=str, default="galsenai/french-wolof-translation",
                        help="Dataset HuggingFace à utiliser")
    parser.add_argument("--split",       type=str, default="train",
                        help="Split à utiliser pour le test (ex: train)")
    parser.add_argument("--test_size",   type=float, default=0.1,
                        help="Proportion du split à utiliser comme test (défaut: 10%%)")
    parser.add_argument("--max_length",  type=int, default=128)
    parser.add_argument("--batch_size",  type=int, default=16)
    parser.add_argument("--num_beams",   type=int, default=4)
    parser.add_argument("--seed",        type=int, default=42)
    parser.add_argument("--num_samples", type=int, default=None,
                        help="Limiter à N exemples (None = tout le test set)")
    parser.add_argument("--output_csv",  type=str, default="evaluation_results.csv",
                        help="Fichier CSV de sortie avec les traductions détaillées")
    parser.add_argument("--output_json", type=str, default="evaluation_metrics.json",
                        help="Fichier JSON de sortie avec les métriques globales")
    return parser.parse_args()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHARGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_model_and_tokenizer(model_path: str):
    print(f"\n📦 Chargement du modèle : {model_path}")
    tokenizer = MarianTokenizer.from_pretrained(model_path)
    model     = MarianMTModel.from_pretrained(model_path)
    device    = "cuda" if torch.cuda.is_available() else "cpu"
    model     = model.to(device)
    model.eval()
    print(f"   ✅ Modèle chargé sur {device.upper()}")
    return model, tokenizer, device


def load_test_data(dataset_name: str, split: str, test_size: float, seed: int, num_samples: int):
    print(f"\n📂 Chargement du dataset : {dataset_name} (split={split})")
    ds = load_dataset(dataset_name)

    # Recréer le split test depuis le split disponible
    split_ds = ds[split].train_test_split(test_size=test_size, seed=seed)
    test_ds  = split_ds["test"]

    if num_samples:
        test_ds = test_ds.select(range(min(num_samples, len(test_ds))))

    print(f"   ✅ {len(test_ds)} exemples de test chargés")
    return test_ds


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRADUCTION PAR BATCH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def translate_batch(texts: list[str], model, tokenizer, device: str,
                    max_length: int, num_beams: int) -> list[str]:
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=max_length,
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_beams=num_beams,
            early_stopping=True,
            no_repeat_ngram_size=3,
            length_penalty=0.8,
        )

    return tokenizer.batch_decode(outputs, skip_special_tokens=True)


def run_inference(test_ds, model, tokenizer, device, max_length, batch_size, num_beams):
    print(f"\n🔄 Génération des traductions (batch_size={batch_size}, num_beams={num_beams})...")
    sources      = test_ds["french"]
    references   = test_ds["wolof"]
    predictions  = []

    start = time.time()
    for i in tqdm(range(0, len(sources), batch_size), desc="Traduction"):
        batch = sources[i : i + batch_size]
        preds = translate_batch(batch, model, tokenizer, device, max_length, num_beams)
        predictions.extend(preds)

    elapsed = time.time() - start
    print(f"   ✅ {len(predictions)} phrases traduites en {elapsed:.1f}s "
          f"({len(predictions)/elapsed:.1f} phrases/s)")
    return sources, references, predictions


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MÉTRIQUES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compute_all_metrics(predictions: list[str], references: list[str]) -> dict:
    print("\n📊 Calcul des métriques...")

    # sacrebleu attend des références en liste de listes
    refs_bleu = [[r.strip()] for r in references]
    preds     = [p.strip() for p in predictions]

    # — BLEU
    bleu   = evaluate.load("sacrebleu")
    b_score = bleu.compute(predictions=preds, references=refs_bleu)

    # — chrF (recommandé pour langues peu dotées)
    chrf   = evaluate.load("chrf")
    c_score = chrf.compute(predictions=preds, references=refs_bleu)

    # — chrF++ (variante qui inclut les mots en plus des caractères)
    chrf2  = evaluate.load("chrf")
    c2_score = chrf2.compute(predictions=preds, references=refs_bleu, word_order=2)

    # — TER
    ter    = evaluate.load("ter")
    t_score = ter.compute(predictions=preds, references=refs_bleu, normalized=True)

    metrics = {
        "bleu"   : round(b_score["score"], 2),
        "chrf"   : round(c_score["score"], 2),
        "chrf++" : round(c2_score["score"], 2),
        "ter"    : round(t_score["score"], 2),   # plus bas = meilleur
        "num_samples": len(predictions),
    }

    return metrics


def score_per_sentence(predictions: list[str], references: list[str]) -> list[float]:
    """Calcule un score chrF par phrase pour identifier les meilleures/pires traductions."""
    chrf = evaluate.load("chrf")
    scores = []
    for pred, ref in zip(predictions, references):
        s = chrf.compute(predictions=[pred.strip()], references=[[ref.strip()]])
        scores.append(round(s["score"], 2))
    return scores


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AFFICHAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_metrics(metrics: dict):
    print("\n" + "═" * 55)
    print("  MÉTRIQUES GLOBALES")
    print("═" * 55)
    print(f"  BLEU    : {metrics['bleu']:>6.2f}   (réf. mondial : >20 = correct)")
    print(f"  chrF    : {metrics['chrf']:>6.2f}   (principal pour le wolof)")
    print(f"  chrF++  : {metrics['chrf++']:>6.2f}   (chrF + ordre des mots)")
    print(f"  TER     : {metrics['ter']:>6.2f}   (plus bas = meilleur, réf. <60)")
    print("─" * 55)
    print(f"  Exemples évalués : {metrics['num_samples']}")
    print("═" * 55)

    # Interprétation automatique
    chrf = metrics["chrf"]
    if chrf >= 60:
        niveau = "🟢 Excellent"
    elif chrf >= 45:
        niveau = "🟡 Correct"
    elif chrf >= 30:
        niveau = "🟠 Modeste"
    else:
        niveau = "🔴 Faible — à améliorer"

    print(f"\n  Appréciation (basée sur chrF) : {niveau}")


def print_examples(sources, references, predictions, scores, n=10):
    print(f"\n{'═'*55}")
    print(f"  EXEMPLES — Top {n//2} meilleures & {n//2} pires traductions")
    print(f"{'═'*55}")

    indexed = sorted(enumerate(scores), key=lambda x: x[1])
    worst   = indexed[:n//2]
    best    = indexed[-(n//2):]

    for label, group in [("❌ PIRES", worst), ("✅ MEILLEURES", best)]:
        print(f"\n  {label}")
        print("─" * 55)
        for idx, score in group:
            print(f"  [chrF={score:.1f}]")
            print(f"  FR  : {sources[idx]}")
            print(f"  REF : {references[idx]}")
            print(f"  GEN : {predictions[idx]}")
            print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SAUVEGARDE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def save_results(sources, references, predictions, scores, metrics,
                 output_csv: str, output_json: str):

    # CSV détaillé — une ligne par exemple
    df = pd.DataFrame({
        "source_fr"    : sources,
        "reference_wo" : references,
        "prediction_wo": predictions,
        "chrf_score"   : scores,
    })
    df = df.sort_values("chrf_score", ascending=False)
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"\n💾 Traductions détaillées sauvegardées : {output_csv}")

    # JSON métriques globales
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"💾 Métriques globales sauvegardées     : {output_json}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    args = parse_args()

    # 1. Chargement
    model, tokenizer, device = load_model_and_tokenizer(args.model_path)
    test_ds = load_test_data(args.dataset, args.split, args.test_size,
                             args.seed, args.num_samples)

    # 2. Inférence
    sources, references, predictions = run_inference(
        test_ds, model, tokenizer, device,
        args.max_length, args.batch_size, args.num_beams
    )

    # 3. Métriques globales
    metrics = compute_all_metrics(predictions, references)
    print_metrics(metrics)

    # 4. Score par phrase
    print("\n⏳ Calcul des scores par phrase (peut prendre 1-2 min)...")
    scores = score_per_sentence(predictions, references)

    # 5. Exemples
    print_examples(sources, references, predictions, scores, n=10)

    # 6. Sauvegarde
    save_results(sources, references, predictions, scores, metrics,
                 args.output_csv, args.output_json)

    print("\n✅ Évaluation terminée !")


if __name__ == "__main__":
    main()