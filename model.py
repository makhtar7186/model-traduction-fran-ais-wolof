import torch
from transformers import (
    MarianMTModel,
    MarianTokenizer,
)


class TranslationModel:
    def __init__(self):
        self.model_dir = "finetuned_fr_wolof"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = MarianMTModel.from_pretrained(self.model_dir).to(self.device)
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_dir)
        
    def translate(self, text: str, num_beams: int = 4) -> str:
        """Traduit une phrase du français vers le wolof."""
        self.model.eval()
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.device)
        with torch.no_grad():
            translated_tokens = self.model.generate(**inputs, num_beams=num_beams, max_length=128)
        return self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]