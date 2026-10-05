# Rožnati koraki & Brkati pohod

Slovenska spletna stran za pohoda v podporo zdravju žensk in moških. Vključuje napovedi, arhiv dogodkov, pet novic in 227 lokalno shranjenih fotografij z Radia Odeon.

## Zagon

Iz korenske mape projekta:

```powershell
python scripts/serve.py
```

Odprite **http://localhost:8080**. Strežnik ustavite s Ctrl+C. Za drug priključek uporabite `python scripts/serve.py --port 8081`. Skripta vedno streže samo mapo `public`, ne glede na delovno mapo.

Za ogled brez strežnika lahko odprete tudi [public/index.html](public/index.html). Povezava z Google Drive zahteva uporabo spletnega strežnika in ustrezno konfiguracijo.

## Struktura projekta

```text
public/                       Spletna stran; vsebino te mape objavite na gostovanju.
  index.html                  Vstopna stran.
  css/styles.css              Oblikovanje in barve iz vabil.
  js/app.js                   Novice, filtri, pojavna okna in galerije.
  data/events.js              Dogodki in nastavitve Google Drive.
  data/news.json              Katalog novic in fotografij.
  data/news.js                Ustvarjena brskalniška različica kataloga.
  data/routes.js              Podatki poti, ustvarjeni iz GPX.
  offline/                    Samostojen offline zemljevid in lokalna podlaga OSM.
  assets/branding/            Znak spletne strani.
  assets/Logo/                Dodani izvirni logotipi pohodov (PNG/PDF).
  assets/vabila/              Spletne kopije vabil.
  assets/novice/              Fotografije po posameznih pohodih.
  assets/gpx/                 Izvirni poti GPX za prikaz in prenos.
  assets/majice/              Fotografije majic za naročilo.
    roznati-koraki/           Majice Rožnatih korakov.
    brkati-pohod/             Majice Brkatega pohoda.
content/news-copy.json        Uredniška besedila povzetkov novic.
content/gallery-exclusions.json Izločene fotografije, ki jih uvoz ne doda nazaj.
gradiva/<leto>/<dogodek>/     Izvirni letaki, slike in PDF-ji.
scripts/                     Lokalni strežnik in uvoz novic.
tests/                       Brskalniška preverjanja in preverjanje fotografij.
docs/UPORABA.md               Podrobna navodila in viri.
.cache/odeon/                 Lokalni predpomnilnik izvornih strani; ni v Gitu.
artifacts/previews/           Posnetki preverjanj; niso v Gitu.
requirements-dev.txt          Python odvisnosti za razvojna orodja.
```

Mapa `public` vsebuje neposredno uporabljene datoteke. Stran ne potrebuje gradnje z npm, baze SQL ali namestitve Python paketov za običajen ogled. Izvirna gradiva, razvojna orodja in predpomnilniki niso del spletne objave.

## Urejanje

- **Napovedi in pohodi:** [public/data/events.js](public/data/events.js).
- **Povzetki novic:** [content/news-copy.json](content/news-copy.json), nato `python scripts/import_odeon.py`.
- **Oblikovanje:** [public/css/styles.css](public/css/styles.css).
- **Poti GPX:** datoteki sta v [public/assets/gpx/](public/assets/gpx/); po spremembi zaženite `python scripts/prepare_routes.py`. [Navodila za poti in zemljevid](docs/POTI.md).
- **Offline zemljevid:** pod potmi kliknite »Prenesi offline zemljevid« in shranjeni HTML odprite v brskalniku brez povezave. Vsebuje obe poti in lokalno podlago. Po spremembi GPX zaženite tudi `python scripts/prepare_offline_map.py`; [navodila](docs/POTI.md#zemljevid-brez-povezave).
- **Majice:** tri oblačila so prikazana v razdelku `#majice`; slike so v [public/assets/majice/](public/assets/majice/), [navodila in podatki za naročanje](docs/MAJICE.md). Prikaz in povezave za povpraševanje urejajte v `public/index.html`.
- **Galerije, viri in podrobna navodila:** [docs/UPORABA.md](docs/UPORABA.md).

Uvozne skripte ne spreminjajo izvirnih gradiv. Fotografije in katalog so že shranjeni v projektu; za običajen zagon strani ponovni uvoz ni potreben.

## Razvojna orodja in preverjanje

Potrebujete Python 3.11 ali novejši. Za uvoz in brskalniška preverjanja namestite odvisnosti v lokalno okolje:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe scripts/import_odeon.py
.venv\Scripts\python.exe tests/check_site.py
```

Brskalniško preverjanje uporablja nameščen Microsoft Edge. Preveri novice, slike, datume, filtre, pojavna okna, mobilni prikaz in pogodbo povezave Google Drive s simuliranimi odgovori. Pravega računa Google ne uporablja.

## Objava

Na statično gostovanje prenesite **vsebino `public/`**, da je `index.html` v korenu spletne objave. Ohranite podmape in imena datotek. Lokalna projektna gradiva ostanejo zunaj objave. Stran trenutno deluje lokalno.
