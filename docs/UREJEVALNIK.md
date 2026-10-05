# Urejevalnik dogodkov in novic

Iz korena projekta zaženite `python3 scripts/serve.py` in odprite **http://localhost:8080/urejevalnik/**. Urejevalnik shranjuje neposredno v projektno mapo in deluje na tem računalniku. Ne potrebuje dodatnih Python paketov. Pri odpiranju HTML z dvoklikom ali na običajnem statičnem gostovanju shranjevanje ni na voljo.

## Nov dogodek

1. Kliknite **+ Nov dogodek**.
2. Vnesite enolično oznako, npr. `roznati-2027`, izberite pohod ter dodajte datum, naslov, zbirno mesto, kratek opis in program. Ura in pot sta neobvezni.
3. Po želji naložite vabilo kot JPG, PNG ali WebP.
4. Kliknite **Shrani spremembe** in osvežite spletno stran.

Datum določa prikaz med aktualnimi dogodki ali v arhivu. Oznake že shranjenega dogodka ni mogoče spreminjati v obrazcu.

## Novica in fotografije

1. Na levi izberite dogodek. Če ga še ni, najprej izpolnite podatke novega dogodka.
2. Označite **Dodaj novico in fotografije**.
3. Vnesite naslov novice, datum objave, povzetek in besedilo. Odstavke ločite s prazno vrstico.
4. Pri viru fotografij vpišite samo ime in priimek ali ime društva oziroma organizacije.
5. Dodajte fotografije. Izberete lahko več slik hkrati. Podprti so JPG, PNG in WebP; posamezna slika je lahko velika največ 15 MB, skupaj pa naenkrat dodajte največ 50 MB novih slik. Večjo galerijo shranjujte po delih.
6. Označite naslovno fotografijo. Po želji dopolnite opise fotografij in povezavo do izvirnega članka.
7. Shranite. Novica se prikaže v razdelku Novice, besedilo in galerija pa tudi pri povezanem dogodku.

Vsak dogodek ima eno novico. Pri obstoječem dogodku z novico obrazec odpre tudi njeno besedilo in fotografije. Gumb **Odstrani iz galerije** odstrani povezavo v galeriji; izvirna slikovna datoteka ostane shranjena. Če urejate dogodek z novico, za prikaz povzetka in zgodbe velja besedilo novice.

## Shranjevanje in kopije

- `public/data/events.json`: dogodki in nastavitve; podatkovni vir urejevalnika.
- `public/data/events.js`: ustvarjena različica dogodkov za spletno stran.
- `public/data/news.json` in `public/data/news.js`: novice in fotografske galerije.
- `content/news-copy.json`: uredniška besedila, posodobljena tudi ob shranjevanju v obrazcu.
- `public/assets/urednik/`: naložene slike z enoličnimi imeni.
- `artifacts/editor-backups/<datum-in-oznaka>/`: kopija podatkovnih datotek pred vsakim shranjevanjem.

Uvoz Radia Odeon ohrani novice, ki so bile shranjene z urejevalnikom. Te imajo v katalogu oznako `editorManaged`.

Za obnovitev ustavite strežnik in iz izbrane varnostne kopije prekopirajte pet podatkovnih datotek nazaj na njihove poti, nato ponovno zaženite strežnik. Naloženih slik pri tem ne brišite.

Spremembe so vidne lokalno. Za posodobitev že objavljene spletne strani prenesite posodobljeno vsebino `public/` na gostovanje. Obrazec za spletno upravljanje s prijavo in shranjevanjem na oddaljenem strežniku zahteva dodatno strežniško namestitev.

## Preverjanje

`python3 tests/check_editor.py` preveri nov dogodek, vabilo, novico, fotografije, naslovno sliko, odstranjevanje fotografij, prikaz na spletni strani, varnostne kopije in mobilni prikaz na začasni kopiji projekta. Za test potrebujete Playwright in njegov Chromium (`python3 -m playwright install chromium`).
