(() => {
  const input = document.querySelector('#article-search');
  if (input) {
    const cards = [...document.querySelectorAll('.post-card')];
    const count = document.querySelector('.result-count');
    const empty = document.querySelector('.empty-state');
    const normalize = value => value.normalize('NFKC').toLocaleLowerCase('ja');
    const filter = () => {
      const terms = normalize(input.value.trim()).split(/\s+/).filter(Boolean);
      let matches = 0;
      cards.forEach(card => {
        const text = normalize(card.dataset.search);
        const found = terms.every(term => text.includes(term));
        card.hidden = !found;
        if (found) matches++;
      });
      count.textContent = `${matches}件の記事`;
      empty.hidden = matches !== 0;
    };
    input.addEventListener('input', filter);
    document.querySelector('.search-form').addEventListener('submit', event => event.preventDefault());
    document.querySelector('.search-form').addEventListener('reset', () => setTimeout(filter, 0));
  }
  const copy = document.querySelector('.copy-url');
  if (copy) copy.addEventListener('click', async () => {
    const status = document.querySelector('.copy-status');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(location.href.split('#')[0]);
      status.textContent = 'コピーしました';
    } catch {
      status.textContent = 'アドレス欄のURLをコピーしてください';
    }
  });
})();
