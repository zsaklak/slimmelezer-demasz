# Területi és mérőkompatibilitás

## Megerősített

| Terület | Elosztói háttér | Mérő | Telegramfejléc | Állapot |
|---|---|---|---|---|
| Magyarország, volt Démász szolgáltatási terület | MVM | Sagem MA309M, háromfázisú | `/SAG5SAG-METER` | Élő raw telegrammal, mérőfotóval, MVM-dokumentummal és automatizált teszttel megerősítve |

A gyártó Sagem, a típus MA309M. A háromfázisú kivitel, az előlap, a kezelőszervek és a P1 port elhelyezése az [MVM Sagemcom MA110M/MA309M ügyféltájékoztatójának](https://mvmhalozat.hu/attachments/39773) MA309M készülékképével egyezik. A helyszíni fotók mérőazonosítót és telepítési részleteket is tartalmaznak, ezért nem részei a nyilvános csomagnak.

## Nincs még megerősítve

- más volt Démász területi mérőtípusok;
- volt ELMŰ területi MVM mérők;
- volt ÉMÁSZ területi MVM mérők;
- más magyar elosztók mérői;
- az egyfázisú Sagemcom MA110M;
- titkosított P1/DSMR telegramok.

Az MVM-csoporthoz tartozás önmagában nem jelent kompatibilitást. A mérőtípus, a firmware, a telegramfejléc, az OBIS-készlet és különösen a `0-0:98.1.0` csoportszerkezete eltérhet.

## Megerősítés feltétele

Egy új terület vagy mérőtípus csak akkor kerülhet a megerősített listába, ha rendelkezésre áll:

1. legalább két, egymást követő, CRC-végződéssel rendelkező telegram szerkezeti ellenőrzése;
2. az OBIS-kódok értékek nélküli listája;
3. a havi profil csoportszáma és mértékegység-sorrendje;
4. ESPHome parserhibák hiánya;
5. Home Assistant entitások és mértékegységek visszaolvasása;
6. legalább 24 órás frissülési próba recorder- vagy koordinátorhiba nélkül.

A jelentéshez használd a GitHub **Mérőkompatibilitási jelentés** hibajegysablonját. Adatvédelmi okból ne csatolj tisztítatlan raw telegramot.
