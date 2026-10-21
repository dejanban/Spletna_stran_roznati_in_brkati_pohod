# Poti in točke pohodov

Razdelek **Poti in točke** (`/#poti`) prikazuje sled Rožnatih korakov ter začetno in končno točko Brkatega pohoda. Povezavi sta tudi pri predstavitvah pohodov.

| Pohod | Prikaz | Podatki |
| --- | --- | --- |
| Rožnati koraki | sled GPX | približno 10,7 km, sklenjena sled; `public/assets/gpx/Roznati-koraki.gpx` |
| Brkati pohod | samo začetna in končna točka | brez sledi GPX in izračuna dolžine |

GPX Rožnatih korakov ostaja na voljo za prenos. Stara sled Brkatega pohoda proti Mirni gori je odstranjena, ker se pohod leta 2026 zaključi na smučišču Gače. Točki nista povezani z navidezno traso.

## Urejanje podatkov

Po spremembah zaženite:

```powershell
python scripts/prepare_routes.py
python scripts/prepare_accessible_content.py
```

Skripti ustvarita `public/data/routes.json`, `public/data/routes.js` in besedilno stran `public/vabila.html`. Uporabljata samo standardno knjižnico Python.

Sled Rožnatih korakov zamenjajte v `public/assets/gpx/Roznati-koraki.gpx`. Razdalja se izračuna kot vsota razdalj med koordinatami po zemeljski površini (Haversinova formula), brez višinskega popravka. Ločeni segmenti se ne povezujejo z navidezno ravno črto. Sklenjena sled ima en segment, njen konec pa je manj kot 50 m od začetka. Preverja se veljavnost koordinat in shrani kontrolna vsota izvornega GPX. Višinski profil ni prikazan.

- **Rožnati koraki – zbor in začetek:** Dobliče 22, 8340 Črnomelj (45.559096, 15.143954); podatki zemljevida so v `MEETING_POINTS` v `scripts/prepare_routes.py`.
- **Brkati pohod – ohranjena začetna točka:** Blatnik pri Črmošnjicah 1, 8333 Semič (45.646197, 15.136487).
- **Brkati pohod – zaključek:** smučišče Gače (45.664092, 15.088865).

Točki Brkatega pohoda se prebereta iz `meetingPoint` in `finishPoint` dogodka `brkati-2026` v `public/data/events.json`. Novo slikovno in PDF-vabilo navajata zbor pred gasilskim domom Črmošnjice; obstoječa začetna točka na zemljevidu je ohranjena po navodilu organizatorja.

## Zemljevid

Pri odpiranju prek HTTP/HTTPS se samodejno prikaže interaktivni zemljevid s podlago OpenStreetMap. Omogoča povečavo, premikanje in prikaz oznak. Rožnati koraki vključujejo sled GPX, Brkati pohod pa samo oznaki začetka in cilja. Podlaga potrebuje internetno povezavo. Gumb pod zemljevidom preklopi na obris poti oziroma prikaz obeh točk brez podlage; ta prikaz deluje tudi pri neposrednem odpiranju datoteke.

Vključena je lokalna kopija **Leaflet 1.9.4** v `public/vendor/leaflet/`, skupaj z licenco. Avtorstvo OpenStreetMap je vidno na zemljevidu. Če podlage ni mogoče naložiti, stran pokaže obvestilo, podatki o pohodu pa ostanejo na voljo. Ploščice se ne prenašajo vnaprej za delo brez povezave.

- [Leaflet – navodila](https://leafletjs.com/examples/quick-start/)
- [Pravila uporabe podlage OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/)

Preverjanje: `python tests/check_routes.py`. Test preveri podatke GPX Rožnatih korakov, začetno in končno točko Brkatega pohoda, odsotnost stare sledi in prenosa, preklapljanje, povečavo in odziv na nedostopno podlago. Posnetki so v `artifacts/previews/`.
