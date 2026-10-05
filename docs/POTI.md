# Poti GPX

Razdelek **Poti GPX** (`/#poti`) prikazuje obe priloženi sledi. Povezavi do posamezne poti sta tudi pri predstavitvah pohodov.

| Pohod | Izvorna datoteka | Dolžina iz koordinat | Potek |
| --- | --- | --- | --- |
| Rožnati koraki | `public/assets/gpx/Roznati-koraki.gpx` | približno 12,8 km | sklenjena sled |
| Brkati pohod | `public/assets/gpx/Brkati-pohod.gpx` | približno 4,5 km | enosmerna sled; brez povratka |

Izvirnika ostaneta nespremenjena in sta na voljo za prenos z gumbom **Prenesi GPX**. To sta splošni priloženi sledi; nista samodejna potrditev zbirnega mesta ali trase konkretnega prihodnjega dogodka. Arhivska poročila o drugih izvedbah zato ohranijo svoje podatke o dolžini poti.

## Urejanje poti

Zamenjajte ustrezno datoteko GPX in iz korena projekta zaženite:

```powershell
python scripts/prepare_routes.py
```

Skripta iz izvirnikov ustvari `public/data/routes.json` in `public/data/routes.js`. Druga datoteka omogoča prikaz obrisa tudi pri neposrednem odpiranju `index.html`. Pri dodatnih poteh je treba dopolniti seznam v skripti in gumbe na spletni strani. Skripta uporablja samo standardno knjižnico Python.

Razdalja se izračuna kot vsota razdalj med koordinatami po zemeljski površini (Haversinova formula), brez višinskega popravka. Ločeni segmenti se ne povezujejo z navidezno ravno črto. Sklenjena sled ima en segment, njen konec pa je manj kot 50 m od začetka. Preverja se veljavnost koordinat. Shranjena je tudi kontrolna vsota izvornega GPX.

Višinski profil ni prikazan: Rožnati koraki imajo 80 točk z višino 0 m, ki bi izračun višinske razlike popačile. Začetna koordinata je označena kot **začetek sledi**, ne kot potrjeno zbirno mesto.

## Zemljevid

Pri odpiranju prek HTTP/HTTPS se samodejno prikaže interaktivni zemljevid s podlago OpenStreetMap pod sledjo GPX. Omogoča povečavo, premikanje ter oznaki začetka in konca. Spletne ploščice potrebujejo internet; lokalna podlaga ostane na voljo ob nedosegljivih ploščicah. Gumb **Prikaži obris poti** preklopi na lokalni obris brez podlage. Pri neposrednem odpiranju datoteke ostaneta na voljo obris in GPX.

Za prikaz je vključena lokalna kopija **Leaflet 1.9.4** v `public/vendor/leaflet/`, skupaj z licenco. Avtorstvo OpenStreetMap je vidno na zemljevidu. Če podlage ni mogoče naložiti, stran pokaže obvestilo, sled in prenos GPX pa ostaneta na voljo. Ploščice se ne prenašajo vnaprej za delo brez povezave.

- [Leaflet – navodila](https://leafletjs.com/examples/quick-start/)
- [Pravila uporabe podlage OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/)

Preverjanje poti: `python tests/check_routes.py`. Test preveri podatke glede na izvirna GPX, preklapljanje, prenos, približevanje in odziv na nedostopno podlago. Posnetki so v `artifacts/previews/`.

## Zemljevid brez povezave

Interaktivni zemljevid na glavni strani naloži tudi shranjeno vektorsko podlago iz `public/offline/podlaga.geojson`. Ta leži pod spletnimi ploščicami: če internetna podlaga odpove, ostanejo vidne lokalne ceste, steze, vodotoki in krajevna imena v okolici obeh poti.

Pod prikazom poti sta gumba **Odpri offline zemljevid** in **Prenesi offline zemljevid**. Prvi odpre trenutno izbrano pot v novem zavihku, drugi shrani `Pohoda-zemljevid-brez-povezave.html`. Datoteka vsebuje obe poti, osnovno kartografsko podlago, kodo za prikaz in izvirni datoteki GPX. Ne potrebuje spremljajočih map, strežnika, predpomnilnika ali internetne povezave.

Pred odhodom prenesite HTML in ga odprite v spletnem brskalniku. Na telefonu uporabite možnost odpiranja datoteke v brskalniku, če privzeti pregledovalnik datotek ne izvaja JavaScripta. Podprti so preklop med pohodoma, premikanje in povečava zemljevida ter prenos GPX. Povezave do zunanjih virov avtorstva potrebujejo internet. Celotna spletna stran se s tem ne shrani za uporabo brez povezave.

Osnovna podlaga vključuje ceste, steze, vodotoke, nekatere površine in krajevna imena okoli obeh sledi z robom približno 1,7 km. Ne vsebuje reliefa, višinskih plastnic, vseh objektov ali načrtovanja novih poti. Premikanje je omejeno na območje izseka. Datum podatkov in avtorstvo sta vidna na zemljevidu.

### Vzdrževanje

- `public/offline/zemljevid.html`: ustvarjen samostojen zemljevid, pripravljen za objavo in prenos.
- `public/offline/podlaga.geojson`: javni izsek podatkov OpenStreetMap (ODbL 1.0), z izvorom, datumom in poizvedbo; ohranite ga pri objavi.
- `content/offline-map.html`: predloga prikaza.
- `public/js/offline-map.js`: risanje lokalne podlage in poti.
- `scripts/prepare_offline_map.py`: priprava končne datoteke, uporablja standardno knjižnico Python.

Po spremembi GPX ali predloge:

```powershell
python scripts/prepare_routes.py
python scripts/prepare_offline_map.py
```

Običajna gradnja uporablja shranjeno podlago in ne dostopa do interneta. Preveri tudi, ali poti še ležijo znotraj izseka. Za osvežitev kartografskih podatkov uporabite `python scripts/prepare_offline_map.py --refresh`. Po potrebi določite drug javni Overpass strežnik z `--endpoint https://overpass-api.de/api/interpreter`.

Če Overpass ni dosegljiv, je za ta majhen izsek na voljo `--refresh --osm-api`. Območje se razdeli na nekaj omejenih zahtevkov uradnemu OSM API; preveliki odgovori se dodatno razdelijo. Prekinjen prenos lahko nadaljujete z dodatnim `--resume`, ki ponovno uporabi odgovore iz `.cache/offline-map/`. Za sveže podatke ta argument izpustite. Ta možnost je namenjena samo majhnemu območju obeh poti, ne prenosu držav ali večjih regij.

Podatki se pridobijo kot omejen vektorski izsek prek [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) ali [OSM API](https://wiki.openstreetmap.org/wiki/API_v0.6), ne s prenosom rastrskih ploščic. Uporabljeni vir je zabeležen v `podlaga.geojson`. OpenStreetMap podatki so na voljo pod [ODbL](https://www.openstreetmap.org/copyright). Lokalni Leaflet je priložen skupaj z licenco BSD-2-Clause; licenca je vključena tudi v preneseni HTML. Vektorska podlaga in izvirni GPX so vgrajeni v končni HTML, zato ohranite navedbe virov pri nadaljnji delitvi.

Preverjanje: `python tests/check_offline_map.py`. Test prenese dejanski HTML s strani, ga odpre iz druge mape brez spremljajočih datotek in z izključeno povezavo ter preveri podlago, obe poti, povečavo, prenosa GPX, ponovno odpiranje in mobilno širino.
