# Dostopnost in obveznosti upravljavca

Spremembe so pripravljene v lokalnem projektu 12. oktobra 2026. Objava uporablja vsebino `public/`. Ta dokument je interni zapis preverjanja in navodilo za upravljavca, ne potrdilo o popolni zakonski skladnosti.

## Izvedene prilagoditve

- Javna izjava `public/dostopnost.html`: obseg, trenutno stanje, nadomestne možnosti, kontakt, rok za odgovor, nadzorni organ ter datum priprave in pregleda.
- Kontakt za povratne informacije uporablja že objavljeni `ckz@zd-crnomelj.si` in telefon `07 30 61 723`. Povezavi do izjave in prijave sta v nogi strani.
- Vseh pet slikovnih vabil ima besedilno različico v podrobnostih dogodka in na `public/vabila.html`. Povezave kod QR so prebrane iz izvirnih vabil in navedene kot običajne spletne povezave.
- Stran z vabili vsebuje bistvene besedilne podatke obeh priloženih poti GPX in deluje brez JavaScripta.
- Vseh 227 lokalnih fotografij ima opis prizora v `public/data/news.json` in brskalniškem katalogu. Opisi ne ugibajo identitete oseb.
- Popravljeni so kontrasti besedila, prikaz fokusa, preskok na vsebino, cilj fokusa po izbiri mobilne navigacije in kroženje fokusa v pojavnem oknu. Escape zapre meni ali pojavno okno.
- Galerije se odprejo brez samodejnega predvajanja. Predvajanje je izrecna izbira; med uporabo galerije s tipkovnico ali kazalcem se ustavi. Ročno menjavo spremlja dostopno obvestilo o številki fotografije.
- Urejevalnik in njegov API zahtevata besedilo slikovnega vabila ter opise novih fotografij. Ob shranjevanju ponovno ustvarita statično besedilno stran.

## Opravljeno preverjanje

Preverjanje je izvedeno v lokalnem Chromiumu, ne na objavljenem gostovanju. Orodje axe-core 4.10.3 uporablja pravila za WCAG 2.0 A/AA, WCAG 2.1 A/AA in dodatne dobre prakse.

- 26 pregledov z axe-core: glavna stran, vse novice, vabila v pojavnih oknih, tri javne strani pri širinah 320, 360, 768 in 1280 px, mobilni meni ter urejevalnik. Zaznanih kršitev ni. [Povzetek avtomatskega pregleda](PREGLED-DOSTOPNOSTI.json) vsebuje rezultate in opozorila za ročni pregled po posameznih prikazih.
- Preizkus dejanske uporabe tipkovnice: preskok na vsebino, odpiranje/zapiranje in kroženje fokusa v dialogu, vračanje na sprožilni gumb, upravljanje fotografij in mobilnega menija.
- Reflow pri širini 320 px, kar preverja postavitev za 400-odstotno povečavo začetnega pogleda s širino 1280 px. Preverjene so tudi prilagoditve razmikov med vrsticami, črkami, besedami in odstavki.
- Besedilni strani vabil in izjave delujeta tudi z izključenim JavaScriptom.
- Obstoječi preizkusi novic, galerij, filtrov, datumov, GPX, zemljevida, shranjevanja in varnosti lokalnega urejevalnika ostajajo uspešni. Google Drive se preverja s simuliranimi odgovori.

Avtomatski pregled ne preveri vseh meril standarda. Opozorila za ročni pregled kontrasta se nanašajo predvsem na simbolne znake, prekrivajoče se ilustracije, kontrole zemljevida in elemente pod lepljivo vrstico urejevalnika. Besedilne alternative so vsebinsko pregledane glede na lokalna vabila in pregledne sličice fotografij.

Celovit preizkus z dejanskimi bralniki zaslona, uporabniki podpornih tehnologij in na objavljeni domeni še ni izveden. Javna izjava zato navaja **delno skladnost**; brez tega pregleda je ne spremenite v brezpogojno trditev o popolni skladnosti. Poleg WCAG je treba pri zaključni presoji upoštevati tudi druge uporabljive zahteve SIST EN 301 549.

## Začetna ocena po 6. členu ZDSMA – osnutek za upravljavca

Predmet ocene: spletišče Rožnati koraki & Brkati pohod, namenjeno objavam pohodov CKZ ZD Črnomelj. Vsebuje napovedi, arhiv, fotografije, informacije o oblačilih in poti GPX. Upravnih storitev in obrazcev za poslovanje z javnostjo v pregledani različici ni.

Tehnična ugotovitev: dostopnost lokalnih vsebin je mogoče izboljšati z besedilnimi različicami, opisi fotografij, semantičnim HTML in prilagoditvami obstoječega oblikovanja ter vedenja. Te prilagoditve so že izvedene. Za pregledane lokalne vsebine ni bila uporabljena izjema zaradi nesorazmernega bremena.

Koristi: uporabniki lahko vabila in osnovne informacije o poteh berejo brez slik ali zemljevida, uporabljajo tipkovnico, nadzorujejo predvajanje galerij in zaprosijo za drugo obliko informacije. Statični HTML omogoča dostop do vabil in izjave tudi brez JavaScripta.

Pred formalnim sprejemom mora upravljavec vnesti dejanske podatke, ki iz izvorne kode niso razvidni:

- uradni naziv upravljavca, objavljena domena in odgovorna oseba;
- finančni viri, notranja organiziranost in razpoložljivo osebje;
- dejanski stroški prilagoditev, zaključnega preverjanja in rednega vzdrževanja;
- ocenjena pogostost in trajanje uporabe ter primerjava stroškov in koristi za uporabnike;
- sklep o oceni, datum sprejema in način hrambe dokumenta.

To je tehnična podlaga za začetno oceno. Ni dokaz, da je upravljavec formalno opravil ali sprejel svojo zakonsko zahtevano oceno. Izjeme za posamezno zahtevo ni mogoče uveljavljati zgolj z navedbo v javni izjavi.

## Obravnava prijav in vzdrževanje

Upravljavec naj določi odgovorno osebo in nadomeščanje za spremljanje kontaktnega predala. Na obvestilo ali prošnjo mora odgovoriti v osmih dneh; če odgovora še ni mogoče podati, mora v tem roku pojasniti zamudo in sporočiti, kdaj bo odgovoril. Prejem, rok in odgovor je treba evidentirati interno. E-poštna povezava na strani sama ne izvaja tega organizacijskega postopka.

Izjavo je treba pregledati najmanj enkrat letno; naslednji redni pregled je najpozneje 12. oktobra 2027. Posodobite jo tudi po večjih spremembah ali ugotovljeni napaki. Za vsako novo slikovno vabilo prepišite pomembne informacije, vključno s povezavami kod QR. Vsaki fotografiji dodajte opis dejanskega prizora, ne zgolj imena datoteke ali imena avtorja. Pri morebitni vključitvi novih albumov Google Drive preverite opise tudi tam.

Opisi uvoženih fotografij so ohranjeni v `content/photo-descriptions.json`, indeksirani po izvornem URL. Uvozni skript jih ob ponovnem uvozu uporabi. Urejevalnik ohranja svoje urejene članke. Po ročnem spreminjanju dogodkov ali podatkov GPX ustvarite statično stran z `python3 scripts/prepare_accessible_content.py`.

## Ponovitev preverjanj

Potrebujete Python in Playwright. `BROWSER_EXECUTABLE` omogoča uporabo lokalnega Chromiuma; brez te nastavitve preizkusi uporabljajo Microsoft Edge. Za avtomatski pregled nastavite `AXE_CORE_PATH` na lokalno datoteko `axe.min.js`. Brez nje se avtomatski del izrecno označi kot izpuščen. Poročilo se privzeto zapiše v `/tmp/pohodi-accessibility-report.json`; drugo pot nastavite z `ACCESSIBILITY_REPORT`.

```bash
python3 tests/check_accessibility.py
python3 tests/check_site.py
python3 tests/check_routes.py
python3 tests/check_editor.py
```

## Viri

- [ZDSMA na PISRS](https://pisrs.si/pregledPredpisa?id=ZAKO7718), predvsem 3. in 5.–8. člen.
- [Pojasnilo inšpektorata o standardu in omejitvah avtomatskih orodij](https://www.gov.si/novice/2023-12-14-vticniki-za-dostopnost/).
- [Inšpektorat za javni sektor](https://www.gov.si/drzavni-organi/organi-v-sestavi/inspektorat-za-javni-sektor/).
- [W3C: besedilne alternative](https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html) in [kontrast besedila](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html).
