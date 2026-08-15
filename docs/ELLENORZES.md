# Ellenőrzési jegyzőkönyv

Dátum: 2026-08-11, Europe/Budapest

## 1.0.1 végponti hibatűrés – helyi ellenőrzés

Dátum: 2026-08-14, Europe/Budapest

A 24 órás élő próba részállapotában három különálló, egyperces Raw
DSMR-végponti időtúllépés jelent meg. A Home Assistant és a két külső
teljesítményforrás közben elérhető maradt; a koordinátorhoz kötött entitások
egy sikertelen frissítéstől átmenetileg `unavailable` állapotúak lettek.

Az 1.0.1 változat helyi ellenőrzésének eredménye:

- egyszeri azonnali HTTP-újrapróbálkozás: sikeres teszt;
- két egymást követő hibás ciklusban az utolsó jó adat megtartása: sikeres
  teszt;
- harmadik hibás ciklustól a hiba továbbadása: sikeres teszt;
- sikeres lekérés után a hibasorozat és a gyorsítótárazott állapot törlése:
  sikeres teszt;
- teljes Python/Home Assistant tesztkészlet: 16/16 sikeres;
- Ruff kód- és formázásellenőrzés: sikeres.

A módosított változat ebben az ellenőrzési lépésben még nem került az élő
Home Assistant rendszerre, ezért az éles újrapróbálkozási viselkedés külön
telepítési és újraindítási kapu után igazolható.

## Élő Raw DSMR Telegram

A csak olvasási ellenőrzés egy volt Démász területi Sagem MA309M mérő SlimmeLezer végpontján futott. A nyilvános jegyzőkönyv nem tartalmaz belső IP-címet, mérési értéket, COSEM-azonosítót vagy mérőazonosítót.

Parancsminta:

```bash
python3 scripts/validate_raw.py \
  --url http://<slimmelezer-cim>/text_sensor/raw_dsmr_telegram
```

Eredmény:

```text
Telegramhossz: 1539/1700
Megfigyelt OBIS-kódok: 50
ESPHome által lefedett kódok: 38
HA-integráció dokumentált raw kódjai: 12
HA-integráció által képzett szenzorok: 31
Automatikusan felismert új OBIS-kódok: 0
Profilcsoportok: 20
Eredmény: SIKERES
```

## ESPHome

- Validáló verzió: ESPHome `2026.7.1`.
- Fordításkor használt parser: `dsmr_parser 1.9.0`.
- `esphome config`: sikeres, `Configuration is valid!`.
- `esphome compile`: sikeres.
- RAM: 36 800 / 81 920 bájt, 44,9%.
- Flash: 423 357 / 1 044 464 bájt, 40,5%.
- A firmware tesztkörnyezetben elkészült, de nem lett telepítve.

## Home Assistant egyedi integráció

- Python szintaktikai fordítás: sikeres.
- Home Assistant `2026.8.1` modulimport: sikeres.
- Teljes Python/Home Assistant tesztkészlet: 13/13 sikeres.
- Ebből parser-egységtesztek: 5/5 sikeres.
- Home Assistant konfigurációs és futásidejű integrációs tesztek: 7/7 sikeres.
- Adatvédelmi jelentés-egységteszt: 1/1 sikeres.
- Induló entitások: 31 raw adat-, 1 számított hálózati nettó
  teljesítmény- és 5 diagnosztikai entitás.
- Szintetikus új OBIS-kód után: 38 entitás, újraindítás nélkül.
- A nettó teljesítmény tesztje `0,250 kW` import és `0,750 kW` export esetén
  `-0,500 kW` eredményt adott, `power` eszköz- és `measurement`
  állapotosztállyal.
- A választható külső forrás tesztje `1,2 kW` import és `300 W` export esetén
  `900 W` nettó értéket adott, majd az exportforrás változására azonnal
  frissült.
- A konfigurációs tesztek igazolják a páros megadás, az eltérő entitások, a
  `power` eszközosztály és a támogatott mértékegység követelményét.
- Egycsoportos és többcsoportos automatikus feldolgozás: sikeres.
- Home Assistant Javítás és előre kitöltött issue-form létrehozása: sikeres.
- Automatikus GitHub-küldés külön tokenkapuja: sikeres.
- Szerkezeti ujjlenyomatos duplikációvédelem: sikeres.
- Mérési érték és belső cím kizárása az eseményből, issue-formból és API-törzsből: sikeres.
- Ruff ellenőrzés és formázás: sikeres.
- Izolált Home Assistant `check_config`: sikeres.
- Hassfest: sikeres, `Integrations: 1`, `Invalid integrations: 0`.
- GitHub Actions `actionlint`: sikeres, hiba nélkül.
- Dokumentációs relatív hivatkozások: 17/17 érvényes.
- Helyi publikációs szerkezetellenőrzés: sikeres, 15 kötelező fájllal.

## Izolált Home Assistant élő próba

- Tesztpéldány: elkülönített, konténeres Home Assistant `2026.5.1`.
- A telepítés előtt a Home Assistant tárhelyfájljairól és a Compose-konfigurációról biztonsági másolat készült.
- A 12 integrációs forrásfájl helyi és távoli SHA-256 értéke fájlonként egyezik.
- A Home Assistant `check_config` ellenőrzés és a kontrollált Core-újraindítás sikeres; a felület ezután HTTP 200 választ adott.
- A korábbi `500 Internal Server Error` oka reprodukálva: a saját URL-validátor nem volt sorosítható a frontend config-flow sémájába.
- Javítás: szabványos Home Assistant URL-selector, külön szerveroldali URL-validálás és magyar/angol mezőhiba.
- A javított config flow frontend-JSON sorosítása sikeres, az élő belső SlimmeLezer-végponttal `create_entry` eredményt adott.
- Az élő lekérés HTTP 200 válaszból 50 OBIS-kódot, 31 raw szenzort és 0 ismeretlen kódot adott; a `0-0:96.13.0` üres tartalma érvényes maradt.
- A végleges config entry a meglévő tulajdonosi fiókkal, a hitelesített Home Assistant API-n keresztül létrejött és betöltődött.
- Visszaolvasott futó állapot: 1 engedélyezett config entry, 36/36 engedélyezett és elérhető entitás, 1 eszköz.
- Visszaolvasott eszközazonosság: gyártó `Sagem`, modell `MA309M + SlimmeLezer`.
- A próba nem küldött GitHub issue-t, és nem módosította az éles Home Assistant konfigurációját.

## GitHub- és HACS-validáció

- Repository-struktúra: helyben előkészítve.
- `manifest.json`: HACS-kötelező mezőkkel kiegészítve.
- `hacs.json`: `country: HU` beállítással elkészítve.
- Új OBIS-regiszter issue-form: elkészítve.
- Az automatikus GitHub-küldés alapértelmezetten kikapcsolt, és csak `Issues: write` tokennel engedélyezhető.
- GitHub Actions: Python, ESPHome, hassfest és HACS munkafolyamat elkészítve.
- Helyi hassfest: sikeres.
- A nyilvános repository első javított GitHub-futásában a Python/Home
  Assistant, ESPHome, hassfest és HACS feladat is sikeres.
- Custom-integration brand ikon: a komponensben megtalálható; a Home Assistant
  Brands repository 2026.3 óta nem fogad új custom-integration ikon-PR-t.
- GitHub Release: a sikeres 24 órás próba után `v1.0.1` verzióval készül.

## Elsődleges Home Assistant előkészített telepítés

- Célrendszer: az elsődleges Home Assistant `2026.7.4` példánya.
- A telepítés előtt Supervisor-mentés készült.
- A 12 integrációs forrásfájl helyi és távoli SHA-256 értéke
  fájlonként egyezik.
- A telepített fájljegyzék SHA-256 ellenőrzése sikeres volt.
- A korábbi komponensverzió külön rollback könyvtárban megmaradt.
- A teljes Home Assistant `ha core check` sikeres.
- A Home Assistant az ellenőrzés után HTTP 200 választ adott.
- A Core indulási ideje az újraindítás nélküli előkészítés alatt nem változott.
- A később külön jóváhagyott Core-újraindítás sikeres volt.
- Az újraindítás után a Home Assistant HTTP 200 választ adott, és a
  napló betöltési hiba nélkül felismerte a custom integrationt.
- A később felvett `slimmelezer_demasz` config entry állapota `loaded`;
  36/36 engedélyezett entitása elérhető.

## 1.0.1 24 órás elfogadási próba

A Zsáklak Home Assistant rendszeren futó 1.0.1 változat külső, percenkénti
próbája 2026-08-14 19:39:00 CEST és 2026-08-15 19:39:11 CEST között sikeresen
lefutott.

- időtartam: 86411 másodperc;
- minták: 1432;
- hibás minta, API-hiba, metaadathiba és forráshiba: 0;
- legnagyobb mintaköz: 81,875 másodperc;
- legnagyobb nettóteljesítmény-képleteltérés: 0,000237 W;
- automatikus Core-helyreállítás és új OBIS-entitás: 0;
- lezáráskori állapot: `loaded`, 38/38 elérhető entitás, élő Recorder-metaadat;
- eredmény: elfogadva.

A próbacsomag nem tartalmaz nyers telegramot vagy mérési értéket. A külső
timer a lezáráskor leállt, a teszttoken eltávolításra került, és Home
Assistant-újraindítás nem történt.

## Zsáklak történeti entitás- és statisztika-migráció

2026-08-12-én a config flow hozzáadása után az élő állapotok és a helyiértékek
ellenőrzése sikeres volt, de az új ESPHome-entitásazonosítók elszakították a
korábbi dashboardokat és Recorder-statisztikákat. A helyreállítás eredménye:

- 23 ESPHome-entitás visszanevezve a korábbi Home Assistant `entity_id`
  értékére;
- 25/25 ellenőrzött mérési és diagnosztikai entitás elérhető, egyik sem
  `unknown` vagy `unavailable`;
- az Energia dashboard két megszűnt diagnosztikai csempéje élő integrációs
  diagnosztikára cserélve;
- az Energy konfiguráció import- és exportforrása a történeti statisztikai
  azonosítót használja;
- 20 statisztikapár, páronként 29, összesen 580 órás rekord importálva a
  történeti adatsorba;
- az aktív 20 történeti statisztikai azonosítón 0 Recorder-validációs hiba;
- egy órás, forrásadatból nem helyreállítható rés dokumentálva, mesterséges
  adatpótlás nélkül;
- a Home Assistant automatizálási, script-, scene- és template-fájljaiban 0
  érintett régi SlimmeLezer-hivatkozás, ezért ezeken nem történt módosítás;
- a művelet alatt Core-újraindítás nem történt.

A migráció előtt Supervisor-mentés, fájlszintű visszaállítási pont és
ellenőrzőösszeggel védett statisztikaexport készült. Ezek belső azonosítói
szándékosan nem részei a nyilvános csomagnak.

Az ESPHome-mintába visszakerült a korábbi `SlimmeLezer Uptime` és
`SlimmeLezer Wi-Fi Signal` szenzor. Ez a repositoryban ellenőrzött következő
firmware-konfiguráció része; az élő eszközre ebben a műveletben nem került
firmware.

## Hálózati nettó teljesítmény – elsődleges példány

2026-08-13-án az integráció kiegészült a `Hálózati nettó teljesítmény`
szenzorral. A számítás közvetlenül a raw telegram `1-0:1.7.0` import- és
`1-0:2.7.0` exportértékéből történik: `import − export`. Az egység `kW`, az
import pozitív, az export negatív.

- 13/13 Python/Home Assistant teszt sikeres;
- Ruff kód- és formázásellenőrzés sikeres;
- publikációs és dokumentációs ellenőrzés sikeres;
- élő raw telegram szerkezeti ellenőrzése sikeres;
- telepítés előtti Supervisor-részmentés és fájlszintű visszaállítási pont
  elkészült;
- a 12 helyi és célrendszerre másolt komponensfájl SHA-256 értéke egyezik;
- `ha core check`: sikeres;
- a külön jóváhagyott Core-újraindítás sikeres;
- a hálózati nettó teljesítmény entitása aktív;
- az entitás `kW`, `power`, `measurement` metaadatai és az `import − export`
  számítás élő visszaolvasással igazoltak;
- az integráció config entry állapota `loaded`, az entitás engedélyezett;
- az indulás után új `slimmelezer_demasz` betöltési vagy futásidejű hiba nem
  jelent meg.

### Home Assistant Energy import/export beállítás javítása

Az Energy dashboard külön import- és exportteljesítmény megadásakor először a
korábbi, már nem létező entitásazonosítókat mentette el. Emiatt az
automatikusan képzett nettó teljesítményszenzor
`unavailable` állapotú volt, és átmenetileg `Statistics not defined` hibát
jelzett.

A támogatott Energy WebSocket API-val beállított import- és exportforrások,
valamint a belőlük képzett nettó szenzor működnek.

Az új nettó szenzor élő, `W`, `power`, `measurement` metaadatú, Recorder-
statisztikai metaadata létrejött. Az Energy validátor végső eredménye 0 hiba.
A régi generált szenzor már nem szerepel az Energy konfigurációban; történeti
metaadatát nem töröltük. A javítás újraindítás nélkül történt.

A módosítás előtt helyi visszaállítási pont készült; annak belső útvonala és
ujjlenyomata szándékosan nem része a nyilvános csomagnak.

## HACS egyedi repository telepítési próba

2026-08-15-én a Zsáklak Home Assistant HACS 2.0.5 példánya egyedi
repositoryként felvette a `zsaklak/slimmelezer-demasz` tárolót. A HACS a
`slimmelezer_demasz` domaint, a `HU` országot és a `v1.0.1` kiadást helyesen
felismerte, majd a kiadást sikeresen telepítette.

- HACS-állapot: telepítve, telepített és elérhető verzió `v1.0.1`;
- a telepített 14/14 komponensfájl SHA-256 értéke egyezik a kiadással;
- config entry: `loaded`;
- integrációs entitások: 38/38 elérhető;
- a kiválasztott nettó szenzor metaadata: `W`, `power`, `measurement`;
- a mértékegységre normalizált `import − export` képlet eltérése
  0,000053 W;
- Recorder-metaadat: élő, átlagképes, `W` egységű;
- a vizsgált naplórészben SlimmeLezer/DSMR hiba nem jelent meg.

A művelet előtt Supervisor-részmentés és külön fájlszintű visszaállítási pont
készült. A telepített kód megegyezett a már futó `v1.0.1` változattal, ezért a
próba Home Assistant-újraindítás nélkül történt. A hivatalos HACS-alaplistára
beadott kérelem: [hacs/default#10011](https://github.com/hacs/default/pull/10011).
