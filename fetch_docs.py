"""Baixa as páginas da タックスアンサー (国税庁) da categoria 確定申告 e salva o texto limpo.

Saída: data/docs.jsonl, uma página por linha: {"id", "title", "url", "text"}.
Fonte: 出典：国税庁ホームページ, sob o 公共データ利用規約（第1.0版）.
"""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.nta.go.jp"
CATEGORY = BASE + "/taxes/shiraberu/taxanswer/code/bunya-kakuteishinkoku.htm"
HEADERS = {"User-Agent": "tax-rag study project"}
OUT = Path("data/docs.jsonl")
PAUSE = 1.0  # segundos entre páginas, pra não martelar o site

# o texto útil começa depois da data de vigência e acaba antes destes cabeçalhos
END_MARKERS = ["関連リンク", "関連コード", "お問い合わせ先", "このコンテンツはお役にたちましたか"]


def get(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "html.parser")


def page_links() -> list[str]:
    soup = get(CATEGORY)
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.fullmatch(r"/taxes/shiraberu/taxanswer/[a-z_]+/\d+\.htm", href) and href not in links:
            links.append(href)
    return links


def clean_text(soup: BeautifulSoup) -> str:
    lines = soup.select_one("#bodyArea").get_text("\n", strip=True).split("\n")
    start = next((i + 1 for i, l in enumerate(lines) if re.match(r"\[.*現在法令等\]", l)), 0)
    end = next((i for i, l in enumerate(lines) if i >= start and l in END_MARKERS), len(lines))
    return "\n".join(lines[start:end])


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    links = page_links()
    print(f"{len(links)} páginas na categoria")
    with OUT.open("w", encoding="utf-8") as f:
        for i, href in enumerate(links, 1):
            url = BASE + href
            soup = get(url)
            title = soup.select_one("h1").get_text(strip=True)
            doc = {"id": Path(href).stem, "title": title, "url": url, "text": clean_text(soup)}
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(links)}] {title} ({len(doc['text'])} caracteres)")
            time.sleep(PAUSE)


if __name__ == "__main__":
    main()
