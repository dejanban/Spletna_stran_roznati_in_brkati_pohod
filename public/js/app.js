"use strict";
(() => {
  const $ = (selector, parent = document) => parent.querySelector(selector);
  const config = window.SITE_CONFIG;
  const news = window.NEWS_DATABASE?.articles || [];
  for (const article of news) {
    if (article.kind === "announcement") continue;
    const event = window.EVENTS.find(item => item.id === article.eventId);
    if (event) {
      event.newsArticle = article;
      if (!event.photos.length) event.photos = article.photos;
      event.paragraphs = article.paragraphs;
      event.summary = article.summary;
      event.reportUrl = article.sourceUrl;
      event.reportLabel = [article.sourceName || "Radio Odeon", article.sourceCredit].filter(Boolean).join(" · ");
    }
  }
  const events = [...window.EVENTS].sort((a, b) => b.date.localeCompare(a.date));
  const escape = (value = "") => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const safeUrl = value => {
    try { const url = new URL(value, document.baseURI); return ["https:", "http:", "file:"].includes(url.protocol) ? escape(url.href) : ""; } catch { return ""; }
  };
  const paragraphHtml = value => String(value).split(/(https?:\/\/[^\s]+)/g).map(part => part.startsWith("https://") || part.startsWith("http://") ? `<a class="source-link" href="${safeUrl(part)}">${escape(part)}</a>` : escape(part)).join("");
  const pointHtml = (point, finish = false) => {
    if (!point) return "";
    const {address, coordinates: [lat, lon]} = point;
    const url = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=16/${lat}/${lon}`;
    return `<p class="${finish ? 'finish-point' : 'meeting-point'}"><strong>${finish ? 'Zaključek pohoda' : 'Zbor in začetek pohoda'}: ${escape(address)}</strong><br>GPS: ${lat.toFixed(6)}, ${lon.toFixed(6)}<br><a class="source-link" href="${safeUrl(url)}" target="_blank" rel="noopener">${finish ? 'Poglej cilj' : 'Poglej zbirno mesto'} na zemljevidu ↗</a></p>`;
  };
  const meetingHtml = event => pointHtml(event.meetingPoint) + pointHtml(event.finishPoint, true);
  const today = () => new Intl.DateTimeFormat("sv-SE", {timeZone: "Europe/Ljubljana", year: "numeric", month: "2-digit", day: "2-digit"}).format(new Date());
  const isPast = event => event.dateIsPublication || event.date < today();
  const dateLabel = event => event.dateIsPublication ? "2023 · iz arhiva" : new Intl.DateTimeFormat("sl-SI", {day: "numeric", month: "long", year: "numeric", timeZone: "Europe/Ljubljana"}).format(new Date(event.date + "T12:00:00+02:00"));
  const typeLabel = event => event.type === "roznati" ? "Rožnati koraki" : "Brkati pohod";
  const publicationLabel = article => new Intl.DateTimeFormat("sl-SI", {day: "numeric", month: "long", year: "numeric"}).format(new Date(article.publishedAt.slice(0,10) + "T12:00:00"));
  let filter = "all", year = "all", disposeGallery = () => {}, lastTrigger;
  const dialog = $("#event-dialog");

  $(".menu-toggle").addEventListener("click", () => {
    const open = $("#navigation").classList.toggle("open");
    $(".menu-toggle").setAttribute("aria-expanded", String(open));
  });
  $("#navigation").addEventListener("click", event => {
    const link = event.target.closest('a[href^="#"]');
    if (link) {
      $("#navigation").classList.remove("open"); $(".menu-toggle").setAttribute("aria-expanded", "false");
      $(link.getAttribute("href"))?.focus({preventScroll: true});
    }
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && $("#navigation").classList.contains("open")) {
      $("#navigation").classList.remove("open"); $(".menu-toggle").setAttribute("aria-expanded", "false");
      $(".menu-toggle").focus();
    }
  });
  [...new Set(events.filter(isPast).map(event => event.date.slice(0, 4)))].forEach(value => {
    const option = document.createElement("option"); option.value = value; option.textContent = value; $("#year-filter").append(option);
  });
  function renderArchive() {
    const selected = events.filter(event => isPast(event) && (filter === "all" || event.type === filter) && (year === "all" || event.date.startsWith(year)));
    $("#event-grid").innerHTML = selected.length ? selected.map(event => `
      <article class="event-card"><button class="event-image ${escape(event.type)}" data-event="${escape(event.id)}" aria-label="Odpri: ${escape(event.title)}">
      ${event.newsArticle ? `<img class="photo-cover" src="${safeUrl(event.newsArticle.cover)}" alt="Fotografija s pohoda: ${escape(typeLabel(event))} ${event.date.slice(0,4)}" loading="lazy"><span class="image-label">Galerija · ${event.newsArticle.photos.length} fotografij</span>` : event.poster ? `<img src="${safeUrl(event.poster)}" alt="Vabilo: ${escape(typeLabel(event))} ${event.date.slice(0,4)}" loading="lazy"><span class="image-label">Izvirno vabilo</span>` : '<span class="archive-graphic" aria-hidden="true">' + escape(event.date.slice(0,4)) + '<small>' + escape(typeLabel(event)) + '</small></span>'}</button>
      <div class="event-meta"><span class="tag ${escape(event.type)}">${escape(typeLabel(event))}</span><span>· ${escape(dateLabel(event))}</span></div><h3>${escape(event.title)}</h3><p>${escape(event.summary)}</p><button class="text-link" data-event="${escape(event.id)}">Zgodba pohoda <span aria-hidden="true">↗</span></button></article>`).join("") : '<p class="empty-results">Za izbrano leto in vrsto še ni objavljenih pohodov. Poskusite drug izbor.</p>';
    $("#result-count").textContent = `Število prikazanih pohodov: ${selected.length}.`;
  }
  $("#news-grid").innerHTML = news.length ? news.map(article => `<article class="news-card"><button class="news-image ${article.kind === "announcement" ? "news-invitation" : ""}" data-news="${escape(article.eventId)}" aria-label="Preberi novico: ${escape(article.title)}"><img src="${safeUrl(article.cover)}" alt="${article.kind === "announcement" ? "Vabilo" : "Utrinek"}: ${escape(article.title)}" loading="lazy"><span class="image-label">${article.kind === "announcement" ? "Vabilo na pohod" : `${article.photos.length} fotografij`}</span></button><p class="news-meta">${escape(article.sourceName || "Radio Odeon")} · ${escape(publicationLabel(article))}</p><h3>${escape(article.title)}</h3><p>${escape(article.summary)}</p><button class="text-link" data-news="${escape(article.eventId)}">${article.kind === "announcement" ? "Preberi vabilo in program" : "Preberi novico in poglej fotografije"} <span aria-hidden="true">↗</span></button></article>`).join("") : '<p>Novice trenutno niso na voljo. Poskusite osvežiti stran.</p>';
  document.querySelectorAll("[data-filter]").forEach(button => button.addEventListener("click", () => {
    filter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach(item => { const active = item === button; item.classList.toggle("active", active); item.setAttribute("aria-pressed", String(active)); });
    renderArchive();
  }));
  $("#year-filter").addEventListener("change", event => { year = event.target.value; renderArchive(); });
  document.querySelectorAll("[data-walk]").forEach(button => button.addEventListener("click", () => {
    year = "all"; $("#year-filter").value = "all"; $(`[data-filter="${button.dataset.walk}"]`).click(); $("#arhiv").scrollIntoView(); $("#arhiv").focus({preventScroll: true});
  }));
  const upcoming = events.filter(event => !isPast(event)).sort((a,b) => a.date.localeCompare(b.date));
  if (upcoming.length) $("#upcoming-content").innerHTML = upcoming.map(event => `<article><span class="status"><span class="little-dot"></span>${event.date === today() ? "DANES" : "PRIHAJAJOČI POHOD"} · ${escape(dateLabel(event))}</span><h3>${escape(event.title)}</h3><p>${escape(event.summary)}</p><p><strong>${escape(event.location)}${event.time ? ` · ob ${escape(event.time)}` : ""}</strong></p><button class="text-link" data-event="${escape(event.id)}">Program in podrobnosti <span aria-hidden="true">↗</span></button></article>`).join("<hr>");

  document.addEventListener("click", event => {
    const newsTrigger = event.target.closest("[data-news]");
    if (newsTrigger) { lastTrigger = newsTrigger; openNews(news.find(item => item.eventId === newsTrigger.dataset.news)); return; }
    const trigger = event.target.closest("[data-event]");
    if (trigger) { event.preventDefault(); lastTrigger = trigger; openEvent(events.find(item => item.id === trigger.dataset.event)); }
  });
  $(".dialog-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
  dialog.addEventListener("close", () => { disposeGallery(); document.body.classList.remove("modal-open"); lastTrigger?.focus(); });
  dialog.addEventListener("keydown", event => {
    if (event.key !== "Tab") return;
    const controls = [...dialog.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')].filter(element => element.getClientRects().length);
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  });

  function openNews(article) {
    if (!article) return;
    if (article.kind === "announcement") {
      openEvent(events.find(item => item.id === article.eventId));
      return;
    }
    disposeGallery();
    const event = events.find(item => item.id === article.eventId);
    if (!event) return;
    $("#dialog-content").innerHTML = `<div class="detail-head"><p class="eyebrow">NOVICE · ${escape(typeLabel(event))}</p><h2 id="dialog-title">${escape(article.title)}</h2><p class="news-publication">Objavljeno: ${escape(publicationLabel(article))}</p></div><div class="news-body">${meetingHtml(event)}${article.paragraphs.map(p => `<p>${escape(p)}</p>`).join("")}</div>${article.sourceUrl ? `<div class="news-source"><p>${escape(article.sourceName || "Radio Odeon")}${article.sourceCredit ? ` · ${escape(article.sourceCredit)}` : ""}</p><a class="source-link" href="${safeUrl(article.sourceUrl)}" target="_blank" rel="noopener">Celoten izvirni članek${article.sourceTitle ? `: ${escape(article.sourceTitle)}` : ""} ↗</a></div>` : ""}<section class="gallery" aria-label="Fotografije pohoda"><h3>Pohod v ${article.photos.length} fotografijah</h3><p class="photo-credit">${escape(article.photoCredit)}</p><div id="gallery-body"></div></section>`;
    document.body.classList.add("modal-open"); dialog.showModal(); dialog.scrollTop = 0;
    setupGallery({...event, photos: article.photos, driveFolderId: ""});
  }

  function openEvent(event) {
    if (!event) return;
    disposeGallery();
    $("#dialog-content").innerHTML = `<div class="detail-head"><p class="eyebrow">${escape(typeLabel(event))} · ${escape(dateLabel(event))}</p><h2 id="dialog-title">${escape(event.title)}</h2></div>
      <div class="detail-layout" ${!event.poster ? 'style="grid-template-columns:1fr"' : ''}>${event.poster ? `<div><a href="${safeUrl(event.poster)}" target="_blank" rel="noopener"><img class="detail-poster" src="${safeUrl(event.poster)}" alt="Izvirno vabilo: ${escape(event.title)}"></a><a class="poster-caption source-link" href="${safeUrl(event.poster)}" target="_blank" rel="noopener">Odpri izvirno vabilo ↗</a></div>` : ""}<div>${meetingHtml(event)}${event.paragraphs.map(p => `<p>${escape(p)}</p>`).join("")}<div class="detail-info"><span>↗ ${escape(event.route || event.location)}</span>${event.time ? `<span>Zbor po vabilu: ${escape(event.time)}</span>` : ""}</div>${event.reportUrl ? `<a class="source-link" href="${safeUrl(event.reportUrl)}" target="_blank" rel="noopener">${escape(event.reportLabel)} ↗</a>` : ""}</div></div>
      ${event.posterText?.length ? `<section class="poster-transcript"><h3>Vabilo v besedilni obliki</h3>${event.posterText.map(p => `<p>${paragraphHtml(p)}</p>`).join("")}<p><a class="source-link" href="mailto:ckz@zd-crnomelj.si">Dodatne informacije: ckz@zd-crnomelj.si</a> · <a class="source-link" href="tel:+38673061723">07 30 61 723</a></p>${event.type === "roznati" ? '<p><a class="source-link" href="vabila.html#roznati-pot">Besedilni opis poti ob Dobličici</a></p>' : ""}</section>` : ""}
      ${isPast(event) ? `<section class="gallery" aria-label="Fotografije pohoda"><h3>Utrinki s pohoda</h3>${event.newsArticle ? `<p class="photo-credit">${escape(event.newsArticle.photoCredit)}</p>` : ""}<div id="gallery-body"></div></section>` : '<p class="calendar-link"><a class="text-link" href="mailto:ckz@zd-crnomelj.si">Vprašajte organizatorja ↗</a></p>'}`;
    document.body.classList.add("modal-open"); dialog.showModal(); dialog.scrollTop = 0;
    if (isPast(event)) setupGallery(event);
  }

  function setupGallery(event) {
    const container = $("#gallery-body");
    const controller = new AbortController();
    const objectUrls = new Set();
    let timer, current = 0, stopped = false, paused = true, photos = [], imageRequest = 0;
    let focused = false, hovered = false;
    const folderId = /^[a-zA-Z0-9_-]+$/.test(event.driveFolderId || "") ? event.driveFolderId : "";
    const clear = () => { clearInterval(timer); timer = undefined; };
    const folderLink = folderId ? `<p style="margin-top:12px"><a class="source-link" href="https://drive.google.com/drive/folders/${encodeURIComponent(folderId)}" target="_blank" rel="noopener">Odpri album v Google Drive ↗</a></p>` : "";
    const visibility = () => { if (document.hidden) clear(); else schedule(); };
    document.addEventListener("visibilitychange", visibility);
    disposeGallery = () => { stopped = true; controller.abort(); clear(); objectUrls.forEach(url => URL.revokeObjectURL(url)); document.removeEventListener("visibilitychange", visibility); };
    function schedule() { clear(); if (!paused && !focused && !hovered && !stopped && photos.length > 1 && !document.hidden) timer = setInterval(() => show(current + 1), Math.max(3000, config.slideshowInterval || 5500)); }
    async function show(index) {
      clear(); current = (index + photos.length) % photos.length;
      const requestId = ++imageRequest, photo = photos[current];
      $(".gallery-counter", container).textContent = `${current + 1} / ${photos.length}`;
      const caption = $(".gallery-caption", container);
      // A shorter caption must not shrink the dialog while its controls are in view.
      caption.style.minHeight = `${caption.getBoundingClientRect().height}px`;
      caption.textContent = photo.caption || photo.name || "Utrinek s pohoda";
      $(".gallery-loading", container).textContent = "Nalagam fotografijo …";
      const img = $(".gallery-frame img", container); img.hidden = true;
      try {
        let url = photo.url;
        if (photo.id) {
          const response = await fetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(photo.id)}?alt=media&key=${encodeURIComponent(config.driveApiKey)}`, {signal: controller.signal});
          if (!response.ok) throw new Error("image");
          const blob = await response.blob();
          if (!blob.type.startsWith("image/")) throw new Error("image");
          if (stopped || requestId !== imageRequest) return;
          url = URL.createObjectURL(blob); objectUrls.add(url);
        } else if (!safeUrl(url)) throw new Error("image");
        if (stopped || requestId !== imageRequest) return;
        const previousUrl = img.dataset.blob;
        img.onload = () => { if (requestId !== imageRequest || stopped) return; img.hidden = false; $(".gallery-loading", container).textContent = ""; schedule(); };
        img.onerror = () => { if (requestId !== imageRequest || stopped) return; $(".gallery-loading", container).textContent = "Fotografije ni mogoče prikazati. Poskusite naslednjo ali odprite album."; };
        img.alt = photo.alt || photo.caption || photo.name || `Fotografija s pohoda ${current + 1}`;
        img.src = url; img.dataset.blob = photo.id ? url : "";
        if (previousUrl) { URL.revokeObjectURL(previousUrl); objectUrls.delete(previousUrl); }
      } catch (error) { if (error.name !== "AbortError" && !stopped && requestId === imageRequest) $(".gallery-loading", container).textContent = "Fotografije ni mogoče naložiti. Poskusite naslednjo ali odprite album."; }
    }
    function renderPhotos() {
      if (!photos.length) { container.innerHTML = `<div class="gallery-empty">Fotografije tega pohoda še niso objavljene.</div>${folderLink}`; return; }
      container.innerHTML = `<div class="gallery-frame"><img alt="" hidden><p class="gallery-loading" role="status"></p></div><p class="gallery-caption"></p><div class="gallery-controls"><button data-prev aria-label="Prejšnja fotografija">←</button><span class="gallery-counter" role="status" aria-live="polite" aria-atomic="true"></span><button data-pause></button><button data-next aria-label="Naslednja fotografija">→</button></div>${folderLink}`;
      const pause = $("[data-pause]", container);
      const setPauseLabel = () => { pause.textContent = paused ? "Predvajaj" : "Ustavi"; pause.setAttribute("aria-label", paused ? "Začni samodejno menjavanje fotografij" : "Ustavi samodejno menjavanje fotografij"); $(".gallery-counter", container).setAttribute("aria-live", paused ? "polite" : "off"); };
      setPauseLabel();
      $("[data-prev]", container).onclick = () => show(current - 1);
      $("[data-next]", container).onclick = () => show(current + 1);
      pause.onclick = () => { paused = !paused; setPauseLabel(); schedule(); };
      container.addEventListener("focusin", () => { focused = true; clear(); });
      container.addEventListener("focusout", event => { if (!container.contains(event.relatedTarget)) { focused = false; schedule(); } });
      container.addEventListener("pointerenter", () => { hovered = true; clear(); });
      container.addEventListener("pointerleave", () => { hovered = false; schedule(); });
      if (photos.length === 1) container.querySelectorAll("button").forEach(button => { button.disabled = true; });
      container.addEventListener("keydown", keyEvent => { if (keyEvent.key === "ArrowLeft" || keyEvent.key === "ArrowRight") { keyEvent.preventDefault(); show(current + (keyEvent.key === "ArrowLeft" ? -1 : 1)); } });
      show(0);
    }
    async function loadDrive() {
      container.innerHTML = '<p class="gallery-loading" role="status">Nalagam album iz Google Drive …</p>';
      try {
        let token = "";
        do {
          const params = new URLSearchParams({key: config.driveApiKey, q: `'${folderId}' in parents and trashed = false and mimeType contains 'image/'`, fields: "nextPageToken,files(id,name)", pageSize: "100", orderBy: "name_natural"});
          if (token) params.set("pageToken", token);
          const response = await fetch(`https://www.googleapis.com/drive/v3/files?${params}`, {signal: controller.signal});
          if (!response.ok) throw new Error("album");
          const data = await response.json(); photos.push(...(data.files || [])); token = data.nextPageToken || "";
        } while (token && !stopped);
        if (!stopped) renderPhotos();
      } catch (error) {
        if (error.name === "AbortError" || stopped) return;
        container.innerHTML = `<p class="gallery-error" role="status">Albuma trenutno ni mogoče naložiti.</p><button class="text-link" data-retry style="margin-top:14px">Poskusi znova ↻</button>${folderLink}`;
        $("[data-retry]", container).onclick = () => { photos = []; loadDrive(); };
      }
    }
    if (folderId && config.driveApiKey) {
      container.innerHTML = `<p class="gallery-empty">Fotografije so shranjene v Google Drive. Z odprtjem galerije se povežete z Googlovo storitvijo.</p><button class="button dark" data-load style="margin-top:14px">Prikaži fotografije ↗</button>${folderLink}`;
      $("[data-load]", container).onclick = loadDrive;
    } else { photos = event.photos || []; renderPhotos(); }
  }
  renderArchive();
})();
