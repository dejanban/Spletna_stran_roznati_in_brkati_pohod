"use strict";
(() => {
  const $ = selector => document.querySelector(selector);
  const form = $('#form');
  const field = name => form.elements.namedItem(name);
  let state, selectedId = null, dirty = false, saving = false, poster = '', posterUpload = null, photos = [], coverIndex = 0;
  const urls = [];
  function status(message, error = false, target = '#save-status') {
    $(target).textContent = message;
    $(target).className = error ? 'error' : 'success';
  }
  const paragraphs = value => value.trim().split(/\n\s*\n/).map(p => p.trim()).filter(Boolean);
  async function load() {
    const response = await fetch('/api/editor');
    if (!response.ok) throw new Error('Urejevalnik zaženite s python3 scripts/serve.py v lokalni projektni mapi.');
    state = await response.json();
    renderList();
    status('Izberite dogodek za urejanje ali dodajte novega.', false, '#status');
  }
  function renderList() {
    $('#events').replaceChildren();
    const search = $('#search').value.toLocaleLowerCase('sl');
    const events = [...state.events].sort((a, b) => b.date.localeCompare(a.date)).filter(e => `${e.title} ${e.date}`.toLocaleLowerCase('sl').includes(search));
    for (const event of events) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'event' + (event.id === selectedId ? ' active' : '');
      button.append(document.createTextNode(event.title));
      const small = document.createElement('small');
      small.textContent = `${event.date} · ${state.articles.some(a => a.eventId === event.id) ? 'Novica in galerija' : 'Dogodek'}`;
      button.append(small); button.onclick = () => select(event); $('#events').append(button);
    }
  }
  function canLeave() { return !dirty || confirm('Spremembe še niso shranjene. Želite nadaljevati brez shranjevanja?'); }
  function select(event = null, force = false) {
    if (saving || (!force && !canLeave())) return;
    urls.splice(0).forEach(url => URL.revokeObjectURL(url));
    form.reset(); selectedId = event?.id || null;
    const article = state.articles.find(a => a.eventId === selectedId);
    for (const key of ['id', 'type', 'date', 'time', 'endTime', 'title', 'location', 'route', 'summary']) field(key).value = event?.[key] || (key === 'type' ? 'roznati' : '');
    field('id').readOnly = Boolean(event);
    field('paragraphs').value = (event?.paragraphs || []).join('\n\n');
    poster = event?.poster || ''; posterUpload = null;
    photos = (article?.photos || []).map(p => ({...p}));
    coverIndex = Math.max(0, photos.findIndex(p => p.url === article?.cover));
    const values = {newsTitle: article?.title || event?.title || '', newsSummary: article?.summary || '', newsParagraphs: (article?.paragraphs || []).join('\n\n'), publishedAt: article?.publishedAt.slice(0,10) || new Intl.DateTimeFormat('sv-SE', {timeZone:'Europe/Ljubljana'}).format(new Date()), photoCredit: article?.photoCredit || '', sourceName: article?.sourceName || (article ? 'Radio Odeon' : 'Organizator'), sourceUrl: article?.sourceUrl || '', sourceTitle: article?.sourceTitle || '', sourceCredit: article?.sourceCredit || ''};
    for (const [key, value] of Object.entries(values)) field(key).value = value;
    $('#publish-news').checked = Boolean(article); $('#publish-news').disabled = Boolean(article);
    toggleNews(); renderPoster(); renderPhotos(); renderList();
    $('#form-title').textContent = event ? 'Uredi dogodek' : 'Nov dogodek'; form.hidden = false; dirty = false;
    status('');
  }
  function toggleNews() {
    const active = $('#publish-news').checked;
    $('#news-fields').hidden = !active;
    for (const name of ['newsTitle', 'publishedAt', 'newsSummary', 'newsParagraphs', 'photoCredit']) field(name).required = active;
  }
  function preview(file) { const url = URL.createObjectURL(file); urls.push(url); return url; }
  function validFiles(files) {
    for (const file of files) if (!['image/jpeg','image/png','image/webp'].includes(file.type) || file.size > 15 * 1024 * 1024) throw new Error('Izberite slike JPG, PNG ali WebP, velike največ 15 MB.');
    const currentSize = photos.reduce((sum, p) => sum + (p.file?.size || 0), 0) + (posterUpload?.size || 0);
    if (currentSize + files.reduce((sum, f) => sum + f.size, 0) > 50 * 1024 * 1024) throw new Error('Naenkrat dodajte največ 50 MB novih slik. Shranite in nato dodajte preostale.');
  }
  function renderPoster() {
    $('#poster-preview').replaceChildren();
    if (poster) { const img = document.createElement('img'); img.src = poster.startsWith('blob:') ? poster : '/' + poster; img.alt = 'Vabilo pohoda'; $('#poster-preview').append(img); }
    $('#remove-poster').hidden = !poster;
  }
  function renderPhotos() {
    $('#photos').replaceChildren();
    photos.forEach((photo, index) => {
      const card = document.createElement('div'); card.className = 'photo';
      const img = document.createElement('img'); img.src = photo.preview || '/' + photo.url; img.alt = photo.caption || `Fotografija ${index + 1}`;
      const label = document.createElement('label'), radio = document.createElement('input');
      radio.type = 'radio'; radio.name = 'cover'; radio.checked = index === coverIndex;
      radio.onchange = () => { coverIndex = index; dirty = true; };
      label.append(radio, document.createTextNode('Naslovna fotografija'));
      const caption = document.createElement('input'); caption.type = 'text'; caption.value = photo.caption || ''; caption.placeholder = 'Opis fotografije'; caption.setAttribute('aria-label', `Opis fotografije ${index + 1}`);
      caption.oninput = () => { photo.caption = caption.value; dirty = true; };
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'secondary'; remove.textContent = 'Odstrani iz galerije';
      remove.onclick = () => { photos.splice(index,1); if (index < coverIndex) coverIndex--; else if (index === coverIndex) coverIndex = 0; dirty = true; renderPhotos(); };
      card.append(img, label, caption, remove); $('#photos').append(card);
    });
  }
  async function encoded(file) {
    return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve({data: reader.result.split(',')[1]}); reader.onerror = () => reject(new Error('Slike ni mogoče prebrati.')); reader.readAsDataURL(file); });
  }
  $('#new').onclick = () => select();
  $('#search').oninput = renderList;
  form.addEventListener('input', () => { dirty = true; });
  $('#publish-news').onchange = () => { dirty = true; toggleNews(); };
  $('#poster-file').onchange = event => {
    try { const file = event.target.files[0]; if (!file) return; validFiles([file]); posterUpload = file; poster = preview(file); dirty = true; renderPoster(); status(''); }
    catch (error) { status(error.message, true); }
    event.target.value = '';
  };
  $('#remove-poster').onclick = () => { poster = ''; posterUpload = null; dirty = true; renderPoster(); };
  $('#photos-file').onchange = event => {
    try { const files = [...event.target.files]; validFiles(files); photos.push(...files.map(file => ({file, preview: preview(file), caption: ''}))); dirty = true; renderPhotos(); status(''); }
    catch (error) { status(error.message, true); }
    event.target.value = '';
  };
  form.onsubmit = async event => {
    event.preventDefault(); if (saving) return;
    const controls = [...form.querySelectorAll('input,select,textarea,button')];
    const previouslyDisabled = new Map(controls.map(c => [c,c.disabled]));
    saving = true; controls.forEach(c => c.disabled = true); $('#new').disabled = true;
    status('Shranjujem …');
    try {
      const record = {};
      for (const key of ['id','type','date','time','endTime','title','location','route','summary']) record[key] = field(key).value;
      record.paragraphs = paragraphs(field('paragraphs').value); record.poster = posterUpload ? '' : poster;
      const payload = {version: state.version, event: record, isNew: !selectedId};
      if (posterUpload) payload.posterUpload = await encoded(posterUpload);
      if ($('#publish-news').checked) {
        if (!photos.length) throw new Error('Novici dodajte vsaj eno fotografijo.');
        payload.article = {title: field('newsTitle').value, summary: field('newsSummary').value, paragraphs: paragraphs(field('newsParagraphs').value), publishedAt: field('publishedAt').value, photoCredit: field('photoCredit').value, coverIndex, photos: []};
        for (const key of ['sourceName','sourceUrl','sourceTitle','sourceCredit']) payload.article[key] = field(key).value;
        for (const photo of photos) payload.article.photos.push(photo.file ? {upload: await encoded(photo.file), caption: photo.caption} : {url:photo.url, caption:photo.caption});
      }
      const response = await fetch('/api/editor/save', {method:'POST', headers:{'Content-Type':'application/json','X-Editor-Token':state.token}, body:JSON.stringify(payload)});
      const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Shranjevanje ni uspelo.');
      dirty = false; await load(); saving = false;
      controls.forEach(c => c.disabled = previouslyDisabled.get(c));
      select(state.events.find(e => e.id === record.id), true); status(result.message);
    } catch (error) { status(error.message, true); }
    finally { saving = false; $('#new').disabled = false; controls.forEach(c => c.disabled = previouslyDisabled.get(c)); $('#publish-news').disabled = state.articles.some(a => a.eventId === selectedId); }
  };
  window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  load().catch(error => { status(error.message, true, '#status'); $('#new').disabled = true; });
})();
