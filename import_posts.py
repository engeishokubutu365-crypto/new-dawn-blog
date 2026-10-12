"""Create Markdown drafts from the publicly retrieved New Dawn article text."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
entries = [
    ('2025-08-11', 'blog-opening', 'ブログページ開設', 'activity', '竹原', 'New Dawnの活動や想いを届けるブログを開設しました。'),
    ('2025-11-21', 'my-path-to-horticultural-therapy', '私が園芸療法士になるまで', 'column', '杉林', '祖父の庭、農業高校、そして大学へ。園芸療法士をめざした原点を綴ります。'),
    ('2025-11-16', 'academic-conference-2025', '日本園芸療法学会に参加しました！', 'research', '竹原', '幸福学4因子を用いた評価方法の可能性について、合同大会で発表しました。'),
    ('2025-12-28', 'shimenawa-workshop', '訪問園芸療法を実施しました！', 'activity', '', '信州産の藁を使ったしめ縄づくり。挑戦や交流が生まれた時間を振り返ります。'),
    ('2026-03-21', 'spring-planting-and-herbal-tea', '訪問園芸療法を実施しました！', 'activity', '', '春の寄せ植えとハーブティー。植物を選び、育て、五感で味わう時間を届けます。'),
]
raw = (ROOT / 'source-extracts.txt').read_text()
chunks = raw.split('\n--------------------------------------------------------------------------------\n')
assert len(chunks) == len(entries), 'Article extraction count mismatch'
mapping = []
for entry, chunk in zip(entries, chunks):
    date, slug, title, category, author, description = entry
    source_url = re.search(r'\((https://www\.newdawn-horticultural\.com/[^\n]+)\)', chunk.splitlines()[0]).group(1)
    lines = [m.group(1) for line in chunk.splitlines() if (m := re.match(r'L\d+: ?(.*)', line))]
    # The first dated heading begins the article; everything earlier is site navigation.
    start = next(i for i, line in enumerate(lines) if line.startswith('### '))
    body = lines[start + 1:]
    end = next((i for i, line in enumerate(body) if line == '## お問い合わせ' or '†概要】' in line), len(body))
    body = body[:end]
    # Page title is displayed once, as the article's h1.
    while body and not body[0].strip(): body.pop(0)
    if body and body[0].startswith('## '): body.pop(0)
    cleaned = []
    for line in body:
        if line.strip() == '##': continue
        line = re.sub(r'【15†PDF†drive\.google\.com】', '[PDF](https://drive.google.com/file/d/1mUs9WFd0I6k_C1Y5ULFZBZ0futXzikom/view?usp=drivesdk)', line)
        line = line.replace('\u00a0', ' ').replace('\ufffc', '')
        assert not re.search(r'【\d+†', line), 'Unresolved retrieved link'
        cleaned.append(line)
    metadata = {'date': date, 'slug': slug, 'title': title, 'category': category, 'author': author, 'description': description, 'source_url': source_url}
    # JSON inside a Markdown front matter block keeps editing dependency-free.
    content = '---\n' + json.dumps(metadata, ensure_ascii=False, indent=2) + '\n---\n\n' + '\n'.join(cleaned).strip() + '\n'
    (ROOT / 'posts' / f'{date}-{slug}.md').write_text(content)
    mapping.append({'date': date, 'source_url': source_url, 'new_path': f'posts/{slug}/', 'category': category})
(ROOT / 'migration-map.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')
print(f'Imported {len(entries)} article drafts')
