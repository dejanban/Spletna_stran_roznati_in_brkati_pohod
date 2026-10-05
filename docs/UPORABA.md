# Rožnati koraki & Brkati pohod

Samostojna slovenska spletna stran, izdelana iz HTML, CSS in JavaScripta. Brez namestitve paketov, zunanjih pisav, analitike ali strežniške baze. Izvirna priložena gradiva ostanejo nespremenjena.

## Odpri stran

Za hiter ogled dvokliknite `public/index.html`. Za razvoj in povezavo z Google Drive priporočamo lokalni strežnik. Iz korenske projektne mape zaženite:

```powershell
python scripts/serve.py
```

Nato odprite <http://127.0.0.1:8080>. Strežnik ustavite s Ctrl+C. Na statično gostovanje prenesite **vsebino mape `public`**. Objave na gostovanje ta lokalna različica ne izvede.

## Urejanje novic in pohodov

Vsi dogodki so v `public/data/events.js`, v seznamu `window.EVENTS`. Urejanje trenutno poteka v tej datoteki, ne prek spletne administracije. Vsak dogodek ima svojo podrobno novico, vabilo, povezavo do poročila in galerijo. Za dodajanje kopirajte obstoječi zapis in mu dodelite enoličen `id`.

### Novice Radia Odeon in lokalna zbirka fotografij

Razdelek **Novice** vsebuje pet objav z lastnimi kratkimi povzetki izvirnih člankov. Klik odpre pojavno okno z besedilom, povezavo do članka, navedbo vira in fotografsko galerijo. Datum ob novici je datum objave članka; datumi pohodov so ločeno prikazani v arhivu.

V projektu je objavljenih **227 fotografij (41,4 MiB)**: Brkati pohod 2023 (20), 2024 (110), 2025 (27) ter Rožnati koraki 2024 (20) in 2025 (50). Slike so shranjene kot izvirne slikovne datoteke in niso odvisne od razpoložljivosti Radia Odeon ali Google Drive.

- `public/assets/novice/<id-pohoda>/`: lokalne fotografije, razvrščene po pohodih.
- `public/data/news.json`: datotečna baza s povzetki, datumom objave, viri, avtorstvom, lokalnimi potmi in kontrolnimi vsotami fotografij.
- `public/data/news.js`: samodejno ustvarjena brskalniška različica iste baze; omogoča tudi ogled z dvoklikom na `index.html` brez strežnika.
- `content/news-copy.json`: besedila povzetkov, ki jih lahko uredite.
- `scripts/import_odeon.py`: uvoz fotografij in izgradnja obeh katalogov. Potrebuje Python pakete `requests`, `beautifulsoup4` in `Pillow`.

Po urejanju `content/news-copy.json` zaženite `python scripts/import_odeon.py` iz korenske mape. Skripta uporabi že prenesene datoteke in preveri njihovo veljavnost; manjkajoče prenese. Predpomnilnik izvornih strani je v `.cache/odeon/`, izključen iz Gita in zunaj mape za objavo. Za osvežitev izvorne strani odstranite le ustrezno datoteko HTML iz tega predpomnilnika pred ponovnim uvozom.

Za pet uvoženih pohodov se povzetki in fotografije ob nalaganju povežejo z dogodki po `eventId`. Za njihovo urejanje uporabite `content/news-copy.json`, saj uvožena vsebina nadomesti osnovni povzetek v `public/data/events.js`. Galerija novice vedno prikazuje lokalno zbirko; galerijo podrobnosti pohoda je še vedno mogoče povezati z Google Drive.

Izločene fotografije so navedene v `content/gallery-exclusions.json` s svojim izvornim URL-jem (`sourceUrl` iz kataloga). Uvoz jih preskoči in ohrani imena preostalih lokalnih datotek. Pri Brkatem pohodu 2024 je izločenih osem fotografij, katerih datoteke so bile odstranjene iz mape. Za nadaljnje izločanje dodajte izvorni URL pod ustrezni `eventId` in ponovno zaženite uvoz; samo brisanje slikovne datoteke pusti nedelujočo povezavo v katalogu.

```javascript
{
  id: "nov-pohod",                 // Enolično ime brez presledkov.
  type: "brkati",                  // "brkati" ali "roznati".
  date: "YYYY-MM-DD",              // Nadomestite s potrjenim datumom.
  time: "08:30",
  title: "Naslov novega pohoda",
  location: "Potrjeno zbirno mesto",
  route: "Opis poti",
  summary: "Kratko besedilo za kartico in napoved.",
  paragraphs: ["Celotno besedilo novice.", "Program in druge informacije."],
  poster: "assets/vabila/ime-vabila.webp", // Ali prazen niz, če vabila ni.
  reportUrl: "",                   // Po izvedbi povezava do poročila.
  reportLabel: "",
  driveFolderId: "",               // Neobvezna mapa Google Drive.
  photos: []
}
```

Prihodnji dogodki in današnji dogodki se pojavijo v razdelku »Aktualno«. Naslednji dan preidejo v arhiv. Datumi se primerjajo po časovnem pasu Europe/Ljubljana ob nalaganju strani. Po izvedbi uredite naslov, povzetek in besedilo v poročilo. Sam datum ni dokaz izvedbe: zapis za 2026 zato jasno pove, da je na voljo program iz vabila in da poročilo še ni dodano. Datum za prvi Brkati pohod je datum objave članka, posebej označen z `dateIsPublication: true`.

## Živa galerija iz Google Drive

Galerija podpira neposredno nalaganje slik iz javne mape prek Google Drive API. Mapa in ključ v dobavljeni različici **nista nastavljena**; resnična povezava zato še ni preizkušena. Dokler fotografij ni, stran pokaže jasno prazno stanje. Letaki se ne predstavljajo kot fotografije s pohodov.

1. Pripravite ločeno mapo s fotografijami, namenjenimi objavi, in omogočite ogled »Vsi s povezavo«. Preverite tudi dovoljenja posameznih datotek. ID mape je del za `/folders/` v povezavi Google Drive.
2. V Google Cloud projektu omogočite Google Drive API in ustvarite API ključ. Ključ omejite na **Google Drive API** in na HTTP referrerje svoje spletne domene (za razvoj po potrebi tudi `http://127.0.0.1:8080/*`). Ta brskalniški ključ je javen; vanj nikoli ne vpisujte OAuth žetonov ali zasebnih poverilnic.
3. V `public/data/events.js` vpišite ključ v `window.SITE_CONFIG.driveApiKey`, ID mape pa v `driveFolderId` ustreznega pohoda.
4. Odprite podrobnosti preteklega pohoda in kliknite »Prikaži fotografije«. Preverite rezultat tudi v zasebnem oknu brez prijave v Google. Omejitve organizacijskega računa, dostopa, prenosov ali kvote lahko nalaganje preprečijo.

Album se prebere ob odprtju galerije, zato se dodane in odstranjene slike upoštevajo ob naslednjem odprtju. Podmape se ne pregledujejo. Vrstni red je naravno razvrščanje po imenih; priporočena so imena `01-…`, `02-…`. Podprti so večstranski seznami datotek. Za splet uporabljajte manjše JPEG/WebP/PNG fotografije: nalaga se izvirna datoteka, ne predogled. HEIC pretvorite v JPEG.

Slike se izmenjujejo vsakih 5,5 sekunde po uspešnem nalaganju; na voljo so prejšnja/naslednja slika, puščični tipki in ustavitev predvajanja. Pri nastavitvi zmanjšanega gibanja je samodejno predvajanje sprva izključeno. Ob zaprtju se prenosi prekinejo in slike sprostijo iz pomnilnika. Napaka pokaže možnost ponovitve in povezavo do albuma.

Dokumentacija: [seznam datotek](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list), [prenos datotek](https://developers.google.com/workspace/drive/api/guides/manage-downloads), [omejitve API ključev](https://cloud.google.com/docs/authentication/api-keys#api_key_restrictions).

### Fotografije brez Google API

Galerija deluje tudi z lokalnimi slikami ali neposrednimi HTTPS povezavami. Pri dogodku pustite `driveFolderId` prazen in dodajte:

```javascript
photos: [
  { url: "assets/fotografije/pohod-01.jpg", caption: "Zbor pohodnikov v Dobličah. Foto: ime avtorja." },
  { url: "assets/fotografije/pohod-02.jpg", caption: "Skupaj ob Dobličici. Foto: ime avtorja." }
]
```

Običajna povezava `drive.google.com/file/d/.../view` ni neposredna slikovna datoteka. Za živo mapo uporabite zgoraj opisani API. Za zasebno mapo bi potrebovali strežniško integracijo z ustrezno prijavo; ta različica je namenjena javno dostopnim fotografijam.

## Viri vsebine

Vsebinska osnova so priloženi letaki 2024–2026 in naslednji članki. Vseh pet člankov je bilo pregledanih ob uvozu novic. Povzetki so kratki in napisani na novo, povezave do izvirnikov in navedbe avtorstva oziroma vira pa so vključene ob novicah in fotografijah.

- [Brkati pohod 2025](https://radio-odeon.com/novice/brkati-pohod-ozavescal-o-zdravju-moskih/)
- [Prvi Brkati pohod, poročilo 2023](https://radio-odeon.com/novice/najbolj-brkati-pohod-v-beli-krajini/)
- [Drugi Brkati pohod 2024](https://www.radio-odeon.com/novice/drugi-najbolj-brkati-pohod-na-mirno-goro-druzenje-zdravje-in-brki/)
- [Rožnati koraki 2025](https://radio-odeon.com/novice/roznati-koraki-za-zdravje-pogum-in-povezanost/)
- [Rožnati koraki 2024](https://radio-odeon.com/novice/roznati-koraki-v-doblicah/)

Kontakt organizatorja je prepisan iz priloženih letakov. Uporabnik je naknadno potrdil nov datum Brkatega pohoda: **21. november 2026**. Dogodek je dodan med napovedi; ura, zbirno mesto, pot in program še niso potrjeni.

## Preverjanje

`python tests/check_site.py` iz korenske projektne mape zažene preverjanje v nameščenem Microsoft Edge prek Python Playwright. Preverjeni so filtri, prazni rezultati, današnji/prihodnji/pretekli dogodki, modalno okno in vračanje fokusa, mobilni meni, pet širin zaslona (360–1440 px), prikaz slik in ustavitev samodejnega predvajanja. Simulirani odgovori Drive preverjajo več strani rezultatov, prenos fotografij, zavrnjen dostop, ponovitev in prazen album. Test ne uporablja pravega Google računa.

Preverijo se tudi kontrolne vsote vseh 227 fotografij, upoštevanje izločenih fotografij, odpiranje petih novic, pravilna povezava do vira, prva in zadnja fotografija vsakega albuma ter pojavno okno na mobilniku. Dostop do Radia Odeon je med brskalniškim testom blokiran, da se potrdi neodvisen prikaz lokalno shranjenih fotografij.

Preverjanje je uspešno, brez zaznanih JavaScript napak. Posnetka prikaza sta `artifacts/previews/preview-desktop.png` in `artifacts/previews/preview-mobile.png`. Resnične povezave Google Drive in objave na gostovanje brez ustrezne konfiguracije ni mogoče potrditi.
