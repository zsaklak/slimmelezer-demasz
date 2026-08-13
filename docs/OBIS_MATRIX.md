# OBIS-lefedettségi mátrix

Az élő Sagem MA309M telegramban 50 OBIS-adatsor jelent meg. Az adatkészlet megegyezik az [MVM Sagemcom MA110M/MA309M ügyféltájékoztatójában](https://mvmhalozat.hu/attachments/39773) felsorolt P1-adatkészlettel. Az értékeket és az azonosítókat ez a dokumentum nem tárolja.

## ESPHome DSMR által közvetlenül feldolgozott kódok – 38

| OBIS | Jelentés | ESPHome-mező |
|---|---|---|
| `0-0:1.0.0` | Mérő időbélyeg | `timestamp` |
| `0-0:17.0.0` | Limiter határérték | `electricity_threshold` |
| `0-0:96.3.10` | Megszakítóállapot | `electricity_switch_position` |
| `0-0:96.13.0` | Szolgáltatói hosszú üzenet; az üres tartalom is érvényes | `message_long` |
| `0-0:96.14.0` | Aktuális tarifa | `electricity_tariff` |
| `1-0:1.7.0` | Aktív import teljesítmény | `power_delivered` |
| `1-0:2.7.0` | Aktív export teljesítmény | `power_returned` |
| `1-0:1.8.0–4` | Aktív importenergia, összesen és tarifák | `energy_delivered_*` |
| `1-0:2.8.0–4` | Aktív exportenergia, összesen és tarifák | `energy_returned_*` |
| `1-0:3.8.0` | Meddő importenergia összesen | `total_imported_energy` |
| `1-0:4.8.0` | Meddő exportenergia összesen | `total_exported_energy` |
| `1-0:13.7.0` | Teljesítménytényező összesen | `power_factor` |
| `1-0:33.7.0`, `53.7.0`, `73.7.0` | Teljesítménytényező fázisonként | `power_factor_l1–l3` |
| `1-0:32.7.0`, `52.7.0`, `72.7.0` | Fázisfeszültségek | `voltage_l1–l3` |
| `1-0:31.7.0`, `51.7.0`, `71.7.0` | Fázisáramok | `current_l1–l3` |
| `1-0:31.4.0`, `51.4.0`, `71.4.0` | Fázisonkénti áramhatárok | `current_fuse_l1–l3` |
| `1-0:21.7.0`, `41.7.0`, `61.7.0` | Aktív import teljesítmény fázisonként | `power_delivered_l1–l3` |
| `1-0:22.7.0`, `42.7.0`, `62.7.0` | Aktív export teljesítmény fázisonként | `power_returned_l1–l3` |

A `/SAG5SAG-METER` fejlécből az `identification` szövegszenzor készül; ez nem OBIS-adatsor, ezért nincs benne az 50-es számban.

Az egyedi integráció a már ESPHome által is kezelt `1-0:1.7.0` és
`1-0:2.7.0` értékét nem duplikálja külön raw entitásként, de ezekből képezi a
`Hálózati nettó teljesítmény` szenzort. Képlete: pillanatnyi import mínusz
pillanatnyi export; importnál pozitív, exportnál negatív, mértékegysége `kW`.

## Home Assistant egyedi integráció által feldolgozott kódok – 12

| OBIS | Jelentés | HA-szenzorok száma |
|---|---|---:|
| `0-0:42.0.0` | COSEM logikai készüléknév | 1 |
| `0-0:96.1.0` | Mérő gyári száma, hex formában | 1 |
| `1-0:5.7.0–8.7.0` | Pillanatnyi meddő teljesítmény QI–QIV | 4 |
| `1-0:5.8.0–8.8.0` | Meddő energia QI–QIV | 4 |
| `1-0:15.8.0` | Kombinált hatásos energia `|+A|+|-A|` | 1 |
| `0-0:98.1.0` | Előző hónap végén tárolt profil | 20 |

Összesen: 31 dokumentált Home Assistant-szenzor. A dinamikus parser ezen felül minden új, szabályos OBIS-adatsort automatikusan feldolgoz; a jelenlegi telegramban nincs további ismeretlen kód.

## A `0-0:98.1.0` húsz értékcsoportja

| Index | Jelentés | Egység |
|---:|---|---|
| 0 | Előző hó végi időbélyeg | – |
| 1 | Aktív importenergia összesen | kWh |
| 2 | Aktív importenergia tarifa 1 | kWh |
| 3 | Aktív importenergia tarifa 2 | kWh |
| 4 | Aktív exportenergia összesen | kWh |
| 5 | Aktív exportenergia tarifa 1 | kWh |
| 6 | Aktív exportenergia tarifa 2 | kWh |
| 7 | Meddő importenergia összesen | kvarh |
| 8 | Meddő exportenergia összesen | kvarh |
| 9 | Meddő energia QI | kvarh |
| 10 | Meddő energia QII | kvarh |
| 11 | Meddő energia QIII | kvarh |
| 12 | Meddő energia QIV | kvarh |
| 13 | Kombinált hatásos energia | kWh |
| 14 | Maximum aktív import teljesítmény összesen | kW |
| 15 | Maximum aktív import teljesítmény tarifa 1 | kW |
| 16 | Maximum aktív import teljesítmény tarifa 2 | kW |
| 17 | Maximum aktív export teljesítmény összesen | kW |
| 18 | Maximum aktív export teljesítmény tarifa 1 | kW |
| 19 | Maximum aktív export teljesítmény tarifa 2 | kW |

Az indexelést az élő 20 csoportos telegram, az [MVM Sagemcom MA110M/MA309M dokumentáció](https://mvmhalozat.hu/attachments/39773) energiasorrendje és a dokumentált `1.6.0–2`, illetve `2.6.0–2` maximumregiszterek együtt támasztják alá.

## Szándékosan kikapcsolt mezők

- `active_energy_import_maximum_demand_last_13_months`: a magyar `0-0:98.1.0` formátum miatt parserhibát okoz.
- `equipment_id`: az ESPHome `0-0:96.1.1` kódot vár, a mérő `0-0:96.1.0` kódot küld; ezt az egyedi HA-integráció kezeli.
- `reactive_power_delivered` és `reactive_power_returned`: az ESPHome `3.7.0`/`4.7.0` kódot vár, a mérő `5.7.0–8.7.0` kódokat küld.
- `frequency`: szerepel az MVM készülékdokumentációban, de az ellenőrzött élő telegramban nem jelent meg.
- A generikus ESPHome-minta belga, luxemburgi, izraeli, svájci, gáz-, víz-, hőmennyiségmérő- és hibastatisztikai mezői nem jelentek meg az élő telegramban, ezért nincsenek engedélyezve.
