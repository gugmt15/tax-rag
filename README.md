# tax-rag

A question-answering assistant over the Japanese National Tax Agency's FAQ
(国税庁 タックスアンサー, 確定申告 category), built as a retrieval-augmented
generation (RAG) pipeline, with an evaluation that measures what retrieval adds.

## The problem

Every 確定申告 season, the tax office call center is flooded with the same
questions. The answers are already in the タックスアンサー FAQ, but people
can't find them. The goal: answer a citizen's question **from the FAQ only**,
with a link to the page it came from, and nothing invented.

The hard part is that tax rules change every year. The 令和8年度 reform
(effective 2026-12-01) raised the basic deduction, the part-time income
threshold and the spouse deduction limits, and a language model trained before
it answers confidently with the old numbers.

## Results

10 test questions with an answer key and source page (`eval/prova.jsonl`):
5 on rules changed by the 2026 reform, 5 control questions on long-standing rules.
Answers are graded against the key by a larger model (correct = 1, partial = 0.5).

| | 2026 reform rules | long-standing rules | total |
|---|---|---|---|
| model alone (Claude Haiku) | 0.5 / 5 | 4.5 / 5 | **5 / 10** |
| RAG (same model + retrieved FAQ passages) | 5 / 5 | 5 / 5 | **10 / 10** |

Retrieval alone: the correct FAQ page was ranked 1st for 10/10 questions.

Without retrieval, the model answered the reform questions with pre-reform values
(e.g. basic deduction 95万円 instead of 104万円, part-time threshold 123万円 instead of 178万円).
With retrieval, it quotes the current values and names the tax year they apply to.

A side finding: the grading model itself doubted the answer key on the basic
deduction question, because it also doesn't know the reform. Grading has to
compare against the key, not against what a model believes.

## How it works

```
question ─► e5 embedding ─► top-5 passages (cosine) ─► question + passages ─► Claude ─► answer + source URLs
```

| file | what it does |
|---|---|
| `fetch_docs.py` | downloads the 111 FAQ pages, strips menus and footers → `data/docs.jsonl` |
| `chunk.py` | splits pages into ~500-character passages on line breaks, with ~120 characters of overlap and the page title prepended → `data/chunks.jsonl` (563 passages) |
| `embed.py` | one vector per passage with `intfloat/multilingual-e5-small` (local, free) → `data/vectors.npy` |
| `rag.py` | retrieval and answer generation; the prompt restricts the model to the passages, requires the tax year when amounts differ by year, and asks for citations |
| `evaluate.py` | runs the test in `sozinho` (model alone) or `rag` mode and grades it → `eval/resultado_*.jsonl` |
| `api.py` | FastAPI service: `POST /ask` |

## Run it

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows
pip install -r requirements.txt
echo ANTHROPIC_API_KEY=sk-ant-... > .env

python fetch_docs.py && python chunk.py && python embed.py
python evaluate.py sozinho
python evaluate.py rag
uvicorn api:app --port 8000
```

```bash
curl -X POST localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "会社員で副業の所得が年30万円あります。確定申告は必要ですか？"}'
```

## Limits

- **The test set is small and easy for retrieval.** The 10 questions were written
  from the FAQ pages, so they share the FAQ's vocabulary. Real citizens phrase
  things differently; a larger set of paraphrased questions is the next step.
- **Out-of-scope questions:** only the 確定申告 category was indexed. Asked about
  inheritance tax, the assistant says the indexed pages don't cover it rather than
  inventing an answer, but this was checked by hand, not measured.
- **No hybrid search or reranking yet.** With 10/10 at rank 1 there was nothing
  to fix on this set; they become worth testing once the harder question set exists.
- This is a portfolio project, not tax advice.

## Source

出典：国税庁ホームページ（タックスアンサー）https://www.nta.go.jp/taxes/shiraberu/taxanswer/
Content reused under the 公共データ利用規約 (PDL1.0).
