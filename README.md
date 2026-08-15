# SlimmeLezer Démász

Home Assistant egyedi integráció és ESPHome-konfiguráció magyarországi, volt Démász szolgáltatási területen működő MVM okosmérőkhöz.

> [!IMPORTANT]
> A működés jelenleg kizárólag egy volt Démász területen üzemelő, `SAG5SAG-METER` fejlécű, háromfázisú Sagem MA309M mérővel igazolt. A gyártó Sagem, a típus MA309M; ezt a mérőfotó és az MVM hivatalos MA110M/MA309M tájékoztatójának háromfázisú készülékképe együtt támasztja alá. Más MVM-területeken – például volt ELMŰ vagy ÉMÁSZ területen – a kompatibilitás még nincs megerősítve. Részletek: [területi kompatibilitás](docs/KOMPATIBILITAS.md).

## Miért készült?

A vizsgált Sagem MA309M mérő `0-0:98.1.0` sora 20 értékcsoportos havi profilt küld. Az ESPHome általános `active_energy_import_maximum_demand_last_13_months` mezője más formátumot vár, ezért bekapcsolva `Invalid number` és `Failed to parse telegram` hibát okoz.

A csomag két egymásra épülő részből áll:

1. Az [ESPHome-minta](esphome/slimmelezer_demasz.yaml) csak a mérő által ténylegesen küldött, beépítetten támogatott mezőket engedélyezi. A nem használt funkciók megmaradtak, de indoklással ki vannak kommentelve.
2. A [Home Assistant egyedi integráció](custom_components/slimmelezer_demasz) a SlimmeLezer belső Raw DSMR Telegram webes végpontjából létrehozza az ESPHome által át nem vehető szenzorokat, és automatikusan figyeli az új OBIS-regisztereket.

## Jelenlegi lefedettség

- 50 megfigyelt OBIS-adatsor;
- 38 adat közvetlenül az ESPHome DSMR komponensből;
- 12 további raw OBIS-kódból 31 Home Assistant-szenzor;
- 1 számított hálózati nettó teljesítményszenzor, importnál pozitív és
  exportnál negatív előjellel;
- 5 adatérték nélküli diagnosztikai szenzor;
- a `0-0:98.1.0` havi profil 20 külön szenzorra bontva;
- új egy- vagy többértékes OBIS-regiszterek automatikus entitásfelvétele;
- egyetlen koordinált HTTP-kérés 10 másodpercenként.

### Átmeneti végponthibák kezelése

Az integráció egy sikertelen Raw DSMR-lekérés után 0,25 másodperccel egyszer
azonnal újrapróbálkozik. Ha mindkét kísérlet sikertelen, az első két egymást
követő frissítési ciklusban megtartja az utolsó jó adatot, így egy rövid
Wi-Fi-, mDNS- vagy ESPHome-webszerver-késés nem teszi azonnal elérhetetlenné az
összes koordinált entitást. A harmadik egymást követő sikertelen ciklustól az
entitások `unavailable` állapotba kerülnek, hogy tartós hibánál ne maradjon
észrevétlenül régi adat a felületen.

A napló a hiba fázisát és kivételtípusát is rögzíti, de nem írja ki a raw
telegramot vagy annak mérési értékeit. A letölthető diagnosztika tartalmazza az
egymást követő és összes hibás frissítés, valamint az utolsó jó adattal
kiszolgált frissítések számát.

A részletes megfeleltetés az [OBIS-mátrixban](docs/OBIS_MATRIX.md) található.

### Hálózati nettó teljesítmény

Az integráció a `1-0:1.7.0` pillanatnyi import- és a `1-0:2.7.0`
pillanatnyi exportteljesítményből egy `Hálózati nettó teljesítmény` szenzort
képez. A számítás `import − export`, ezért a hálózatból vételezett teljesítmény
pozitív, a hálózatba visszatáplált teljesítmény negatív. A szenzor egysége
`kW`, eszközosztálya `power`, állapotosztálya `measurement`, így a Home
Assistant Energy dashboard hálózati teljesítmény mezőjében kiválasztható.

### Választható külső import- és exportteljesítmény

Az integráció beállításainál opcionálisan kiválasztható egy Home Assistant
import- és egy exportteljesítmény-szenzor. Ez azért nem kötődik konkrét
gyártóhoz vagy mérőtípushoz, mert a SlimmeLezeren kívüli mérési eszköz nem
ismert előre.

Az integráció csak `sensor` domainű, `power` eszközosztályú entitásokat kínál
fel. A két forrást együtt kell megadni, és nem lehetnek azonosak. A létrejövő
`Kiválasztott nettó teljesítmény` szenzor képlete `import − export`; fogyasztás
esetén pozitív, termelés/visszatáplálás esetén negatív. A támogatott
teljesítményegységeket automatikusan `W`-ra alakítja, és bármelyik forrás
kiesésekor `unavailable` állapotba kerül.

Beállítás: **Beállítások → Eszközök és szolgáltatások → SlimmeLezer Démász →
Beállítások**. A funkció kikapcsolásához mindkét választót üresen kell hagyni.

## Fontos: a HACS csak a Home Assistant-részt telepíti

A HACS a `custom_components/slimmelezer_demasz` integrációt telepíti, az ESPHome firmware-konfigurációt nem.

Az integráció működéséhez a SlimmeLezer firmware-ben szükséges:

- a Raw DSMR Telegram `internal: true` beállítása, hogy ne legyen túl hosszú Home Assistant-entitásállapot;
- a `web_server.include_internal: true` beállítása, hogy a raw szöveg a helyi webes végponton mégis lekérdezhető legyen;
- az inkompatibilis `active_energy_import_maximum_demand_last_13_months` mező kikapcsolása;
- megfelelő, jelenleg 1700 karakteres UART- és telegrambuffer.

Az indokolt teljes minta innen tölthető le:

[`esphome/slimmelezer_demasz.yaml`](https://github.com/zsaklak/slimmelezer-demasz/blob/main/esphome/slimmelezer_demasz.yaml)

## Telepítés

### ESPHome

1. Készíts biztonsági másolatot a jelenlegi SlimmeLezer YAML-ról.
2. Másold át az [ESPHome-mintát](esphome/slimmelezer_demasz.yaml).
3. Hozd létre az `esphome/secrets.yaml` fájlt a
   [példa](esphome/secrets.example.yaml) alapján (ha még nem lenne).
4. Futtasd a **Validate**, majd a **Compile** műveletet.
5. Az OTA-telepítés előtt ellenőrizd újra a célkészülék azonosságát.

### Home Assistant kézi telepítése

Másold a következő könyvtárat:

```text
forrás: custom_components/slimmelezer_demasz/
cél:    /config/custom_components/slimmelezer_demasz/
```

A Home Assistant újraindítása után válaszd:

**Beállítások → Eszközök és szolgáltatások → Integráció hozzáadása → SlimmeLezer Démász**

Részletes leírás: [Home Assistant-telepítés](docs/HOME_ASSISTANT_TELEPITES.md).

### HACS

A HACS csak a Home Assistant-integrációt telepíti; az ESPHome YAML-t külön kell
alkalmazni a fenti indoklás szerint. A HACS-validáció, a 24 órás élő próba és
az egyedi repositoryból végzett `v1.0.1` telepítési próba sikeres. A hivatalos
HACS-alaplistára beadott [felvételi kérelem](https://github.com/hacs/default/pull/10011)
karbantartói elbírálásra vár. A részletes kiadási állapot a
[HACS-dokumentációban](docs/HACS.md) követhető.

## Automatikus OBIS-figyelés

Az integráció minden lekérdezéskor összehasonlítja az aktuális telegramot a már ismert szenzorkulcsokkal. Egy új OBIS-sor vagy új értékcsoport megjelenésekor futás közben új, stabil egyedi azonosítójú entitást hoz létre.

Az automatikus leképezés szándékosan óvatos: ismert mértékegységnél beállítja a megfelelő Home Assistant eszközosztályt, ismeretlen jelentésnél azonban nem talál ki mérési szemantikát.

Minden új, nem dokumentált OBIS-kódhoz automatikusan létrejön:

- egy tartós Home Assistant **Javítás** bejegyzés;
- egy adatvédelmileg tisztított `slimmelezer_demasz_new_obis` esemény;
- egy előre kitöltött GitHub **Új OBIS-regiszter** issue-form.

A jelentés kizárólag az OBIS-kódot, a csoportszámot, a mértékegységeket, az értéktípusokat, a kikövetkeztetett osztályokat, a telegramfejlécet és egy szerkezeti ujjlenyomatot tartalmaz. Mérési érték, mérőazonosító, forrás-URL, hostnév és IP-cím nem kerül bele.

Alapértelmezetten a GitHub-beküldés emberi jóváhagyást igényel. Az integráció **Beállítások** oldalán külön bekapcsolható a teljesen automatikus küldés. Ehhez kizárólag a `zsaklak/slimmelezer-demasz` repositoryra korlátozott, `Issues: write` jogosultságú finomhangolt GitHub-token használható. A sikeresen elküldött szerkezeti ujjlenyomatot a Home Assistant privát tárhelye megjegyzi, ezért ugyanazt a jelentést nem küldi el ismételten.

Az automatikus küldés csak a nyilvános GitHub repository létrehozása után működhet.

## Tesztelés

Parser és formátum:

```bash
python3 -m unittest discover -s tests -p 'test_parser.py' -v
ruff check custom_components tests scripts
ruff format --check custom_components tests scripts
```

Home Assistant futásidejű teszt:

```bash
PYTHONPATH=. pytest -q
```

Csak olvasási élő telegram-ellenőrzés:

```bash
python3 scripts/validate_raw.py
```

Az ellenőrzőprogram nem írja ki a mérési értékeket vagy mérőazonosítókat. A legutóbbi eredmények: [ellenőrzési jegyzőkönyv](docs/ELLENORZES.md).

## Dokumentáció

- [OBIS-lefedettségi mátrix](docs/OBIS_MATRIX.md)
- [ESPHome-konfiguráció indoklása](docs/ESPHOME.md)
- [Home Assistant-telepítés](docs/HOME_ASSISTANT_TELEPITES.md)
- [Területi és mérőkompatibilitás](docs/KOMPATIBILITAS.md)
- [HACS-előkészítés és beadási kapuk](docs/HACS.md)
- [Ellenőrzési jegyzőkönyv](docs/ELLENORZES.md)
- [Közreműködési útmutató](CONTRIBUTING.md)

## Források

- [MVM – Sagemcom MA110M és MA309M ügyféltájékoztató](https://mvmhalozat.hu/attachments/39773)
- [ESPHome DSMR komponens](https://esphome.io/components/sensor/dsmr/)
- [ESPHome webkiszolgáló](https://esphome.io/components/web_server/)
- [Home Assistant integrációfejlesztési dokumentáció](https://developers.home-assistant.io/docs/creating_integration_file_structure/)
- [Home Assistant Repairs fejlesztői dokumentáció](https://developers.home-assistant.io/docs/core/platform/repairs/)
- [GitHub Issues REST API és tokenjogosultság](https://docs.github.com/en/rest/issues/issues#create-an-issue)
- [HACS integráció-közzétételi követelmények](https://hacs.xyz/docs/publish/integration/)

## Állapot

A projekt az [MIT licenc](LICENSE) feltételeivel használható. A `v1.0.1`
kiadás és a HACS egyedi repository-próba ellenőrzötten sikeres. A HACS
alapértelmezett tárolói közé történő felvétel a
[hacs/default#10011](https://github.com/hacs/default/pull/10011) karbantartói
összevonására vár.
