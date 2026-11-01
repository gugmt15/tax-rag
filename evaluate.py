"""Passa a prova (eval/prova.jsonl) e dá a nota.

Modos:
  sozinho  o modelo responde só com o que já sabe (a linha de base)
  rag      o modelo responde com os trechos achados na FAQ (vem depois)

A correção é feita por um modelo maior, que compara a resposta com o gabarito.
"""
import json, sys
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()
MODELO = "claude-haiku-5-5"
CORRETOR = "claude-sonnet-5-5"

SISTEMA_SOZINHO = "日本の所得税などに関する質問に、日本語で簡潔に答えてください。"

CORRECAO = """質問、正解、回答を比べて採点してください。
正解の要点（数値・条件）がすべて合っていれば「正解」、一部だけ合っていれば「部分正解」、
間違っているか答えていなければ「不正解」。
1行目に判定だけ（正解／部分正解／不正解）、2行目に短い理由を書いてください。

質問: {pergunta}
正解: {gabarito}
回答: {resposta}"""


def texto(r):
    return "".join(b.text for b in r.content if b.type == "text")


def responder_sozinho(pergunta):
    r = client.messages.create(model=MODELO, max_tokens=10000, system=SISTEMA_SOZINHO,
                               messages=[{"role": "user", "content": pergunta}])
    return texto(r)


def corrigir(item, resposta):
    r = client.messages.create(model=CORRETOR, max_tokens=1000, messages=[{"role": "user",
        "content": CORRECAO.format(pergunta=item["pergunta"], gabarito=item["gabarito"], resposta=resposta)}])
    linhas = texto(r).strip().splitlines()
    return linhas[0].strip(), " ".join(linhas[1:]).strip()


def responder_rag(pergunta):
    from rag import responder
    return responder(pergunta)["resposta"]


PONTOS = {"正解": 1.0, "部分正解": 0.5, "不正解": 0.0}

if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "sozinho"
    responder = {"sozinho": responder_sozinho, "rag": responder_rag}[modo]
    prova = [json.loads(l) for l in open("eval/prova.jsonl", encoding="utf-8")]
    saida = []
    for item in prova:
        resposta = responder(item["pergunta"])
        nota, motivo = corrigir(item, resposta)
        saida.append({**item, "resposta": resposta, "nota": nota, "motivo": motivo})
        print(f'{item["id"]} [{item["tipo"]}] {nota}  {motivo[:90]}')
    total = sum(PONTOS.get(s["nota"], 0) for s in saida)
    for tipo in ("nova", "controle"):
        parte = [s for s in saida if s["tipo"] == tipo]
        print(f"{tipo}: {sum(PONTOS.get(s['nota'],0) for s in parte)}/{len(parte)}")
    print(f"nota {modo}: {total}/{len(saida)}")
    Path(f"eval/resultado_{modo}.jsonl").write_text(
        "".join(json.dumps(s, ensure_ascii=False) + "\n" for s in saida), encoding="utf-8")
