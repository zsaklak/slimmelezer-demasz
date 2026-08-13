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
- saját Home Assistant Brands-bejegyzés;
- legalább a repositoryba csomagolt `brand/icon.png` arculati elem;
- teljes GitHub Release, nem csak címke.

## Tervezett GitHub-metaadatok

- repository: `zsaklak/slimmelezer-demasz`;
- leírás: `Home Assistant és ESPHome támogatás volt Démász területi MVM Sagem MA309M okosmérőkhöz`;
- témakörök: `home-assistant`, `hacs`, `esphome`, `dsmr`, `p1-meter`, `obis`, `mvm`, `demasz`, `hungary`, `sagem`, `ma309m`;
- első kiadás: `v1.0.0`.

## Emberi kapuk

1. Nyílt forráskódú licenc kiválasztása és jóváhagyása. **Teljesítve: MIT.**
2. A GitHub repository létrehozása és a `main` ág publikálása.
3. A GitHub Actions első sikeres futása.
4. Kézi telepítés egy teszt Home Assistant-példányra. **Teljesítve.**
5. Legalább 24 órás élő próba.
6. Home Assistant Brands-bejegyzés.
7. `v1.0.0` GitHub Release.
8. Először HACS egyedi repositoryként végzett telepítési próba.
9. Csak ezután PR a HACS alapértelmezett repository-listájába.

A lokális forráskód, tesztek, dokumentáció és CI-konfiguráció elkészült. A
repository publikálása után a GitHub Actions eredménye, a 24 órás élő próba,
a Brands-bejegyzés, a kiadás és a HACS-beadás külön ellenőrzési lépés.
