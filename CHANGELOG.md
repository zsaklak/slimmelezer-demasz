# Változásnapló

## 1.0.0 – kiadásra előkészítve

- Volt Démász területi Sagem MA309M ESPHome-minta.
- 38 közvetlen ESPHome DSMR-mező.
- 31 Home Assistant-szenzor 12 raw OBIS-kódból.
- A 20 csoportos `0-0:98.1.0` havi profil biztonságos feldolgozása.
- Új OBIS-regiszterek automatikus felismerése és entitásfelvétele.
- Tartós Home Assistant Javítás és előre kitöltött GitHub issue-form új OBIS-kódhoz.
- Alapértelmezetten kikapcsolt, tokennel engedélyezhető automatikus GitHub-jelentés.
- Érték-, azonosító- és hálózaticím-mentes jelentési formátum, szerkezeti ujjlenyomatos duplikációvédelemmel.
- Magyar konfigurációs felület és dokumentáció.
- HACS- és hassfest-validációra előkészített repository-struktúra.
- Javított, frontendben is sorosítható config flow szabványos URL-selectorral.
- A gyártó és a típus egyértelműsítve: Sagem, MA309M.
- Hálózati nettó teljesítményszenzor a pillanatnyi import és export
  különbségéből; import pozitív, export negatív előjellel.
- Opcionálisan kiválasztható külső import- és exportteljesítmény-entitások,
  automatikus egységnormalizálással és élő nettó teljesítményszenzorral.
