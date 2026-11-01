"""Um vetor por pedaço (data/chunks.jsonl -> data/vectors.npy), com o multilingual-e5.

O e5 foi treinado com prefixo: "passage: " no documento e "query: " na pergunta.
Os vetores saem normalizados, então o produto escalar já é a similaridade de cosseno.
"""
import json
import numpy as np
from sentence_transformers import SentenceTransformer

MODELO_VETOR = "intfloat/multilingual-e5-small"

if __name__ == "__main__":
    chunks = [json.loads(l) for l in open("data/chunks.jsonl", encoding="utf-8")]
    modelo = SentenceTransformer(MODELO_VETOR)
    vetores = modelo.encode(["passage: " + c["text"] for c in chunks],
                            normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    np.save("data/vectors.npy", vetores.astype(np.float32))
    print(f"{len(chunks)} vetores de dimensão {vetores.shape[1]} em data/vectors.npy")
