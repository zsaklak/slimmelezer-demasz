# HACS-előkészítés és beadási kapuk

## Mit telepít a HACS?

A HACS kizárólag a `custom_components/slimmelezer_demasz` Home Assistant-integrációt telepíti. Az ESPHome-konfigurációt nem másolja a SlimmeLezerre, ezért a HACS leírásának kötelező része:

- a magyar `0-0:98.1.0` formátum és az általános ESPHome-mező inkompatibilitásának magyarázata;
- a Raw DSMR Telegram `internal: true` és `web_server.include_internal: true` beállításának indoka;
- a teljes ESPHome-minta forráslinkje:
  `https://github.com/zsaklak/slimmelezer-demasz/blob/main/esphome/slimmelezer_demasz.yaml`;
- a jelenlegi, kizárólag volt Démász területre megerősített kompatibilitás.
- az ismeretlen OBIS-kódok helyi Javítás/issue-form folyamatának, valamint az alapértelmezetten kikapcsolt automatikus GitHub-küldésnek az adatvédelmi és tokenfeltételei.
- az opcionális, gyártófüggetlen import- és exportteljesítmény-entitás
  választásának, előjelének és egységnormalizálásának leírása.

A gyökérben található magyar `README.md` tartalmazza ezeket, így HACS alatt is ez jelenik meg információs oldalként.

Az automatikus GitHub-küldés nem HACS-telepítési feltétel és alapértelmezetten ki van kapcsolva. Bekapcsolásakor a felhasználó kifejezetten engedélyezi a szerkezeti OBIS-metaadat továbbítását, és saját, repositoryra korlátozott `Issues: write` tokenjét adja meg.

## Repository-követelmények

- egyetlen integráció a `custom_components/` alatt;
- gyökérszintű `README.md` és `hacs.json`;
- `manifest.json` legalább domain, név, codeowner, dokumentáció, hibajegykezelő és verzió mezőkkel;
- `hacs.json` fájlban `country: HU`;
- nyilvános GitHub repository, leírás, témakörök és engedélyezett Issues;
- sikeres HACS Action és hassfest;
- a custom integration saját `brand/icon.png` és `brand/icon.svg` arculati
  elemei;
- teljes GitHub Release, nem csak címke.

2026.3 óta a Home Assistant Brands repository nem fogad új
`custom_integrations` bejegyzéseket: az arculati elemek közvetlenül a custom
componentben adhatók meg. A Brands repository ezt külön automatizmussal
ellenőrzi és az új custom-integration ikon-PR-eket lezárja, ezért ehhez a
projekthez nem készül külön Brands PR.

## Tervezett GitHub-metaadatok

- repository: `zsaklak/slimmelezer-demasz`;
- leírás: `Home Assistant és ESPHome támogatás volt Démász területi MVM Sagem MA309M okosmérőkhöz`;
- témakörök: `home-assistant`, `hacs`, `esphome`, `dsmr`, `p1-meter`, `obis`, `mvm`, `demasz`, `hungary`, `sagem`, `ma309m`;
- első nyilvános kiadás: `v1.0.1`.

## Emberi kapuk

1. Nyílt forráskódú licenc kiválasztása és jóváhagyása. **Teljesítve: MIT.**
2. A GitHub repository létrehozása és a `main` ág publikálása. **Teljesítve.**
3. A GitHub Actions első sikeres futása. **Teljesítve.**
4. Kézi telepítés egy teszt Home Assistant-példányra. **Teljesítve.**
5. Legalább 24 órás élő próba. **Teljesítve: 86411 másodperc, 1432/1432 hibamentes minta.**
6. Custom-integration brand ikon. **Teljesítve; külön Brands PR már nem fogadott.**
7. `v1.0.1` GitHub Release. **Teljesítve.**
8. Először HACS egyedi repositoryként végzett telepítési próba. **Teljesítve a Zsáklak Home Assistant rendszeren.**
9. Csak ezután PR a HACS alapértelmezett repository-listájába. **Beadva: [hacs/default#10011](https://github.com/hacs/default/pull/10011); karbantartói elbírálásra vár.**

A forráskód, tesztek, dokumentáció, CI-konfiguráció, kézi telepítés, a
24 órás élő próba, a GitHub Release és a HACS egyedi repository-próba
elkészült. A HACS-alaplista felvételi kérelmének összevonása külső
karbantartói human gate.
