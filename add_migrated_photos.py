"""Insert the archived article photographs at their original text positions."""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PHOTOS=json.loads((ROOT/'photo-migration.json').read_text())
DESCRIPTIONS={
 'academic-conference-2025': ['オレンジ色の花を並べた記事の装飾写真','幸福学4因子を示す発表スライド','評価方法の集計例を示す発表スライド','園芸療法における幸福学4因子を用いた評価方法の可能性の発表タイトル','合同大会での口述発表と会場の様子','夕日を背景に咲く花の写真'],
 'blog-opening':['ピンク色のバラが咲く庭の写真'],
 'my-path-to-horticultural-therapy':['花壇で土と植物に触れて作業する様子','草花が咲く花壇の写真','枝を切る作業の様子','植物のそばでの園芸作業の様子','花壇で植物を手入れする様子','草花のそばで苗を手に持つ様子'],
 'shimenawa-workshop':['しめ縄づくりの工程を説明する様子','藁を扱ってしめ縄を作る様子','テーブルに固定した藁をなう作業','しめ縄に飾りを付ける作業','完成したしめ縄の作品'],
 'spring-planting-and-herbal-tea':['パンジーなど春の草花を使った寄せ植え','春の草花を鉢に植え込む作業','土と草花を使った寄せ植えの作業','活動で用意したハーブの葉や枝','花壇に芽吹いた植物の写真','春の寄せ植えを作る活動の様子'],
}

def normalized_with_positions(text):
    positions=[];out=[]
    # Match source-visible link labels while omitting their Markdown URL syntax.
    replacements={m.start():(m.end(),m[1],m.start()+1) for m in re.finditer(r'\[([^\]]+)\]\([^)]+\)',text)}
    i=0
    while i<len(text):
        if i in replacements:
            end,label,start=replacements[i]
            chars=[(c,start+j) for j,c in enumerate(label)];i=end
        else:
            chars=[(text[i],i)];i+=1
        for char,pos in chars:
            for c in unicodedata.normalize('NFKC',char):
                if not c.isspace() and c not in '*#\ufffc':out.append(c);positions.append(pos)
    return ''.join(out),positions

by_article=defaultdict(list)
for photo in PHOTOS:
    photo['alt']=DESCRIPTIONS[photo['article']][photo['number']-1]
    by_article[photo['article']].append(photo)

for slug,photos in by_article.items():
    path=next((ROOT/'posts').glob('*-'+slug+'.md'))
    metadata,body=path.read_text().removeprefix('---\n').split('\n---\n',1)
    data=json.loads(metadata)
    if any(photo['file'] in body for photo in photos):raise ValueError(f'{slug}: photographs already inserted')
    normalized,positions=normalized_with_positions(body)
    insertions=defaultdict(list)
    for photo in photos:
        token,_=normalized_with_positions(photo['anchor'])
        needle=token[-48:]
        match=normalized.rfind(needle)
        if match<0:
            # No photo silently falls back to an unrelated paragraph.
            raise ValueError(f'{slug} image {photo["number"]}: anchor not found: {needle}')
        position=positions[match+len(needle)-1]+1
        end_of_line=body.find('\n',position)
        if end_of_line>=0:position=end_of_line
        insertions[position].append(f'![{photo["alt"]}]({photo["file"]})')
    for position in sorted(insertions,reverse=True):
        body=body[:position]+'\n\n'+'\n\n'.join(insertions[position])+body[position:]
    cover=photos[0]
    data['cover_image']=cover['file'];data['cover_alt']=cover['alt']
    path.write_text('---\n'+json.dumps(data,ensure_ascii=False,indent=2)+'\n---\n'+body)
    print(f'{slug}: inserted {len(photos)} photographs')

(ROOT/'photo-migration.json').write_text(json.dumps(PHOTOS,ensure_ascii=False,indent=2)+'\n')
