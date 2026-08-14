# Home Assistant – SlimmeLezer Démász egyedi integráció

Az integráció a SlimmeLezer belső, weben elérhető `Raw DSMR Telegram` végpontját olvassa. Egyetlen koordinált HTTP-kéréssel:

- létrehozza a jelenleg ismert, ESPHome által át nem vehető 31 szenzort;
- létrehozza a `Hálózati nettó teljesítmény` számított szenzort az import és
  export pillanatnyi teljesítmény különbségéből;
- nem duplikálja az ESPHome DSMR platformon már létrejövő 38 OBIS-adatsort;
- minden új, szabályos OBIS-sor értékcsoportjához automatikusan új szenzort hoz létre;
- mértékegység alapján lehetőség szerint automatikusan beállítja a Home Assistant eszköz- és állapotosztályát;
- öt diagnosztikai szenzorral jelzi az OBIS-kódok, a raw-ból képzett szenzorok, az ismeretlen kódok, a telegramhossz és a sikeresen beküldött GitHub-jelentések számát;
- az új, korábban nem ismert OBIS-kódokat értékek nélkül beírja a Home Assistant naplójába;
- a letölthető diagnosztikába csak a kódokat és darabszámokat teszi, mérési értéket és mérőazonosítót nem.

A hálózati nettó teljesítmény előjel-konvenciója: `import − export`. Pozitív
érték esetén a ház a külső hálózatból vételez, negatív értéknél a külső
hálózatba táplál vissza. A `kW`, `power`, `measurement` metaadatok miatt a
szenzor a Home Assistant Energy dashboard hálózati teljesítményforrásaként
használható.

## Választható külső teljesítményforrások

Az integráció **Beállítások** oldalán opcionálisan kiválasztható egy
importteljesítmény- és egy exportteljesítmény-entitás. A választók a Home
Assistant `sensor` domainjének `power` eszközosztályú entitásait kínálják fel,
így a funkció nem feltételez konkrét külső mérőt vagy gyártót.

Szabályok:

- mindkét entitást meg kell adni, vagy mindkettőt üresen kell hagyni;
- az import és export nem lehet ugyanaz az entitás;
- a forrásoknak támogatott teljesítményegységet kell használniuk;
- a számítás `import − export`, tehát fogyasztás pozitív, export negatív;
- a források `mW`, `W`, `kW`, `MW`, `GW`, `TW` vagy `BTU/h` egysége
  automatikusan `W`-ra konvertálódik;
- bármelyik forrás hiányakor vagy nem numerikus állapotánál a képzett szenzor
  nem elérhető.

Az opció mentése csak az integrációt tölti újra, teljes Home Assistant
Core-újraindítás nem szükséges.

## Átmeneti Raw DSMR-végponthibák

Minden frissítési ciklus legfeljebb két HTTP-kísérletet végez, a kettő között
0,25 másodperc várakozással. Ha mindkettő sikertelen, az integráció legfeljebb
két egymást követő frissítési cikluson át az utolsó jó adatot tartja elérhető
állapotban. A harmadik sikertelen ciklustól a koordinátorhoz tartozó entitások
`unavailable` állapotúak lesznek. Egy 10 másodperces lekérdezési időköznél ez
nagyjából 20 másodperces türelmi időt jelent a két ciklusban végzett
újrapróbálkozások futási idején felül.

A Home Assistant naplója a `http_timeout`, `http`, `json`, `payload` vagy
`telegram` hibafázist és a kivétel típusát közli. A diagnosztikai letöltésben
az alábbi, mérési értéket nem tartalmazó mezők segítik a hibakeresést:

- `using_stale_data`;
- `consecutive_failed_refreshes`;
- `total_failed_refreshes`;
- `stale_refreshes`;
- `last_failure_stage` és `last_failure_type`.

## Telepítés

Másold ezt a teljes könyvtárat:

```text
forrás: custom_components/slimmelezer_demasz/
cél:    /config/custom_components/slimmelezer_demasz/
```

Ezután a Home Assistant Core újraindítása szükséges. A felületen:

1. **Beállítások → Eszközök és szolgáltatások → Integráció hozzáadása**.
2. Keresd meg: **SlimmeLezer Démász**.
3. Alapértelmezett végpont: `http://slimmelezer.local/text_sensor/raw_dsmr_telegram`.
4. Alapértelmezett lekérdezési időköz: 10 másodperc.

A telepítés, a konfiguráció módosítása és a Core újraindítása külön emberi jóváhagyási kapu. A projekt előkészítése ezeket nem hajtja végre.

## Automatikus regiszterfigyelés

Az integráció minden sikeres lekéréskor összeveti a telegram aktuális szenzorkulcsait a már ismert kulcsokkal. Új OBIS-kód vagy új értékcsoport esetén az entitás futás közben, újraindítás nélkül létrejön. Az egyedi azonosító a SlimmeLezer forrásazonosítójából, az OBIS-kódból és szükség esetén a csoportszámból készül, ezért a következő újraindításkor is ugyanaz marad.

Az automatikus leképezés konzervatív:

- `kWh`/`Wh`: energia;
- `kvarh`/`varh`: meddő energia;
- `kW`/`W`: teljesítmény;
- `kvar`/`var`: meddő teljesítmény;
- `V`, `A`, `Hz`, `%`, `m3`/`m³`: a megfelelő szenzorosztály;
- ismeretlen egységnél az eredeti egység megmarad, de nem kap találomra eszközosztályt;
- több zárójeles értékcsoportból külön szenzorok készülnek.

A `0-0:98.1.0` nem általános automatikus mező: a Sagem MA309M 20 csoportos havi profiljaként, dokumentált sorrendben bomlik 20 szenzorra. Eltérő csoportszám esetén az egész frissítés hibára fut, így nem rendelünk téves jelentést a mezőkhöz.

## Új OBIS-kód ellenőrzése és GitHub-jelentése

Új, nem dokumentált kód megjelenésekor az integráció automatikusan létrehoz egy tartós bejegyzést a **Beállítások → Rendszer → Javítások** felületen. A **További információ** hivatkozás megnyitja az előre kitöltött GitHub **Új OBIS-regiszter** űrlapot.

A Home Assistant eseménybuszán `slimmelezer_demasz_new_obis` esemény is keletkezik. Ez automatizáláshoz használható, és csak a következő szerkezeti adatokat tartalmazza:

- OBIS-kód és értékcsoportszám;
- mértékegységek és szám/szöveg értéktípusok;
- kikövetkeztetett eszköz- és állapotosztályok;
- szerkezeti ujjlenyomat;
- az előre kitöltött issue-form címe.

Mérési érték, mérőazonosító, raw telegram, SlimmeLezer URL, hostnév és IP-cím nem kerül az eseménybe vagy a GitHub-jelentésbe.

Az alapértelmezett mód kézi: a felhasználó átnézi és elküldi az űrlapot. Az automatikus küldés bekapcsolása:

1. **Beállítások → Eszközök és szolgáltatások → SlimmeLezer Démász → Beállítások**.
2. Kapcsold be az automatikus GitHub-jelentést.
3. Adj meg egy kizárólag a `zsaklak/slimmelezer-demasz` repositoryra korlátozott finomhangolt tokent, amelynek egyetlen szükséges repositoryjogosultsága `Issues: write`.

A token a Home Assistant konfigurációjában tárolódik, a diagnosztikából kimarad, de a Home Assistant biztonsági mentése tartalmazhatja. Az automatikus küldés kikapcsolásakor a token törlődik az integráció beállításaiból. A már sikeresen elküldött szerkezeti ujjlenyomatok privát helyi tárba kerülnek, így ugyanaz az eltérés újraindítás után sem generál új GitHub issue-t.

## Ellenőrzés

Helyi parser-tesztek:

```bash
python3 -m unittest discover -s tests -v
```

Teljes Home Assistant futásidejű próba (fejlesztői tesztkörnyezetben):

```bash
PYTHONPATH=. pytest -q
```

Ez ellenőrzi a 31 raw adat-, 1 DSMR-alapú nettó teljesítmény- és 5
diagnosztikai entitás létrejöttét, valamint bekapcsolt opció esetén a választott
forrásokból képzett további nettó szenzort. Ezután futás közben bead egy új, `Hz` egységű
OBIS-regisztert, és bizonyítja a 38. entitás automatikus felvételét. Külön
tesztek igazolják a Javítás létrejöttét, az automatikus GitHub-küldés
bekapcsolási kapuját, a duplikációvédelmet és azt, hogy mérési érték vagy belső
cím nem kerül a jelentésbe.

Élő, csak olvasási ellenőrzés a SlimmeLezerrel:

```bash
python3 scripts/validate_raw.py
```

Az ellenőrzőprogram nem írja ki a mérési értékeket vagy a mérőazonosítókat.
