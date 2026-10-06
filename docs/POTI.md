# Poti GPX

Razdelek **Poti GPX** (`/#poti`) prikazuje obe priloženi sledi. Povezavi do posamezne poti sta tudi pri predstavitvah pohodov.

| Pohod | Izvorna datoteka | Dolžina iz koordinat | Potek |
| --- | --- | --- | --- |
| Rožnati koraki | `public/assets/gpx/Roznati-koraki.gpx` | približno 10,7 km | sklenjena sled |
| Brkati pohod | `public/assets/gpx/Brkati-pohod.gpx` | približno 4,5 km | enosmerna sled; brez povratka |

Izvirnika ostaneta nespremenjena in sta na voljo za prenos z gumbom **Prenesi GPX**. To sta splošni priloženi sledi; nista samodejna potrditev zbirnega mesta ali trase konkretnega prihodnjega dogodka. Arhivska poročila o drugih izvedbah zato ohranijo svoje podatke o dolžini poti.

## Urejanje poti

Zamenjajte ustrezno datoteko GPX in iz korena projekta zaženite:

```powershell
python scripts/prepare_routes.py
```

Skripta iz izvirnikov ustvari `public/data/routes.json` in `public/data/routes.js`. Druga datoteka omogoča prikaz obrisa tudi pri neposrednem odpiranju `index.html`. Pri dodatnih poteh je treba dopolniti seznam v skripti in gumbe na spletni strani. Skripta uporablja samo standardno knjižnico Python.

Razdalja se izračuna kot vsota razdalj med koordinatami po zemeljski površini (Haversinova formula), brez višinskega popravka. Ločeni segmenti se ne povezujejo z navidezno ravno črto. Sklenjena sled ima en segment, njen konec pa je manj kot 50 m od začetka. Preverja se veljavnost koordinat. Shranjena je tudi kontrolna vsota izvornega GPX.

Višinski profil ni prikazan. Začetna koordinata je označena kot **začetek sledi**, ne kot potrjeno zbirno mesto.

## Zemljevid

Pri odpiranju prek HTTP/HTTPS se samodejno prikaže interaktivni zemljevid s podlago OpenStreetMap pod sledjo GPX. Omogoča povečavo, premikanje ter oznaki začetka in konca. Podlaga potrebuje internetno povezavo. Gumb **Prikaži obris poti** preklopi na obris brez podlage. Pri neposrednem odpiranju datoteke ostaneta na voljo obris in GPX.

Za prikaz je vključena lokalna kopija **Leaflet 1.9.4** v `public/vendor/leaflet/`, skupaj z licenco. Avtorstvo OpenStreetMap je vidno na zemljevidu. Če podlage ni mogoče naložiti, stran pokaže obvestilo, sled in prenos GPX pa ostaneta na voljo. Ploščice se ne prenašajo vnaprej za delo brez povezave.

- [Leaflet – navodila](https://leafletjs.com/examples/quick-start/)
- [Pravila uporabe podlage OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/)

Preverjanje poti: `python tests/check_routes.py`. Test preveri podatke glede na izvirna GPX, preklapljanje, prenos, približevanje in odziv na nedostopno podlago. Posnetki so v `artifacts/previews/`.
