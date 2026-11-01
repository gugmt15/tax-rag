"""Corta as páginas da FAQ (data/docs.jsonl) em pedaços (data/chunks.jsonl).

Cada pedaço tem uns 500 caracteres, cortado em fim de linha, com as últimas
linhas do pedaço anterior repetidas no começo (sobreposição), pra regra que
cai na fronteira não ficar partida ao meio. O título da página vai na frente
de cada pedaço: sem ele, um pedaço do meio da página não diz de que assunto é.
"""
import json

TAMANHO = 500
SOBREPOE = 120


def cortar(doc):
    linhas = [l for l in doc["text"].split("\n") if l.strip()]
    pedacos, atual = [], []
    for linha in linhas:
        if atual and sum(len(l) for l in atual) + len(linha) > TAMANHO:
            pedacos.append(atual)
            resto, n = [], 0
            for l in reversed(atual):
                if n + len(l) > SOBREPOE:
                    break
                resto.insert(0, l)
                n += len(l)
            atual = resto
        atual.append(linha)
    if atual:
        pedacos.append(atual)
    return [{"id": f'{doc["id"]}-{i}', "doc_id": doc["id"], "title": doc["title"], "url": doc["url"],
             "text": doc["title"] + "\n" + "\n".join(p)} for i, p in enumerate(pedacos)]


if __name__ == "__main__":
    docs = [json.loads(l) for l in open("data/docs.jsonl", encoding="utf-8")]
    chunks = [c for d in docs for c in cortar(d)]
    with open("data/chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    tam = sorted(len(c["text"]) for c in chunks)
    print(f"{len(docs)} páginas -> {len(chunks)} pedaços; tamanho mediano {tam[len(tam)//2]}, maior {tam[-1]}")
