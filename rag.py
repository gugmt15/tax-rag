"""O RAG: acha os pedaços da FAQ mais perto da pergunta e responde só com eles.

    pergunta -> vetor -> os K pedaços mais perto -> pergunta + pedaços -> modelo -> resposta com a fonte
"""
import json
import numpy as np
from dotenv import load_dotenv
import anthropic
from sentence_transformers import SentenceTransformer

from embed import MODELO_VETOR

load_dotenv()
MODELO = "claude-haiku-5-5"
K = 5

SISTEMA = """あなたは国税庁タックスアンサーの案内係です。
与えられた【資料】だけを根拠に、日本語で簡潔に答えてください。
資料に答えがない場合は「タックスアンサーの該当ページでは確認できませんでした」と答え、推測で補わないでください。
年分によって金額が違う場合は、どの年分の金額かを明記してください。
最後に、根拠にした資料の番号を「出典: [1][3]」のように書いてください。"""

_chunks = [json.loads(l) for l in open("data/chunks.jsonl", encoding="utf-8")]
_vetores = np.load("data/vectors.npy")
_modelo_vetor = SentenceTransformer(MODELO_VETOR)
_client = anthropic.Anthropic()


def buscar(pergunta, k=K):
    q = _modelo_vetor.encode(["query: " + pergunta], normalize_embeddings=True)[0]
    notas = _vetores @ q
    melhores = np.argsort(-notas)[:k]
    return [{**_chunks[i], "score": float(notas[i])} for i in melhores]


def responder(pergunta, k=K):
    trechos = buscar(pergunta, k)
    material = "\n\n".join(f"[{i+1}] {t['text']}\n(URL: {t['url']})" for i, t in enumerate(trechos))
    r = _client.messages.create(model=MODELO, max_tokens=2000, system=SISTEMA, messages=[{"role": "user",
        "content": f"【資料】\n{material}\n\n【質問】\n{pergunta}"}])
    texto = "".join(b.text for b in r.content if b.type == "text")
    fontes = list(dict.fromkeys(t["url"] for t in trechos))
    return {"resposta": texto, "trechos": trechos, "fontes": fontes}
