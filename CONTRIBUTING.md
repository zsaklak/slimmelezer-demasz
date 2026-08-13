# Közreműködés

Ez a projekt jelenleg egy volt Démász területi Sagem MA309M mérő élő telegramja alapján készült. Különösen értékesek a más MVM-területről vagy más mérőtípusról érkező, adatvédelmileg megtisztított kompatibilitási jelentések.

## Kompatibilitási jelentés

Nyiss hibajegyet a **Mérőkompatibilitási jelentés** sablonnal, és add meg:

- az MVM területét vagy a korábbi elosztót;
- a mérő gyártóját és pontos típusát;
- a telegram fejlécét;
- az ESPHome verzióját;
- az OBIS-kódok listáját értékek nélkül;
- a `0-0:98.1.0` csoportszámát és mértékegység-sorrendjét, ha jelen van.

Ne küldj nyilvánosan mérő gyári számot, COSEM-azonosítót, Wi-Fi-adatot, belső IP-címet, API-kulcsot vagy teljes, tisztítatlan raw telegramot.

## Fejlesztési ellenőrzés

```bash
python3 -m unittest discover -s tests -p 'test_parser.py' -v
PYTHONPATH=. pytest -q
ruff check custom_components tests scripts
ruff format --check custom_components tests scripts
```

Új OBIS-mezőhöz szükséges:

1. anonimizált szerkezeti bizonyíték;
2. dokumentált jelentés és mértékegység;
3. parser-teszt;
4. OBIS-mátrix frissítése;
5. visszafelé kompatibilis egyedi azonosító.

Külső import/export teljesítményforrás módosításánál külön tesztelendő a két
választó validációja, az eltérő mértékegységek `W`-ra normalizálása, az
`import − export` előjel és a forrásállapot-változásra történő frissítés.
