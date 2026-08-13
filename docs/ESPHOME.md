# Az ESPHome-konfiguráció indoklása

## A parserhiba oka

A volt Démász területen vizsgált Sagem MA309M mérő a `0-0:98.1.0` OBIS-kód alatt egy időbélyegből, tizenhárom energiaértékből és hat maximumteljesítményből álló, 20 csoportos havi profilt küld. A regisztert és az alapjául szolgáló energiamérő-, valamint maximumteljesítmény-adatokat az [MVM MA110M/MA309M ügyféltájékoztatója](https://mvmhalozat.hu/attachments/39773) is dokumentálja.

Az ESPHome `active_energy_import_maximum_demand_last_13_months` mezője nem ezt a magyar formátumot várja. Ha a mező aktív, a parser az egymást követő zárójeles csoportokat egyetlen számként próbálja értelmezni, majd `Invalid number` és `Failed to parse telegram` hibával elutasítja a teljes telegramot.

Ezért a mező a mintában kikommentelve marad, a havi profilt pedig a Home Assistant egyedi integráció bontja fel.

## Raw telegram: belső, de weben elérhető

```yaml
web_server:
  port: 80
  version: "3"
  include_internal: true

text_sensor:
  - platform: dsmr
    telegram:
      id: raw_dsmr_telegram
      name: "Raw DSMR Telegram"
      internal: true
```

Az `internal: true` megakadályozza, hogy az 1500 karakternél hosszabb telegram Home Assistant-entitásállapot legyen. Az `include_internal: true` eközben megtartja a helyi `/text_sensor/raw_dsmr_telegram` webes végpontot, amelyből az egyedi integráció olvas.

## Kikapcsolt funkciók

A teljes generikus SlimmeLezer szenzorlista megmaradt a YAML-ban, de minden nem használt blokk kommentelt. Ide tartoznak többek között:

- a titkosítási kulcs kezelése, mert a vizsgált telegram titkosítatlan;
- a generikus dashboard-import, hogy ne írja felül a mérőspecifikus konfigurációt;
- belga, izraeli és svájci mérőmezők;
- M-Bus gáz-, víz-, hő- és almérők;
- a telegramban nem szereplő kimaradási és hálózatminőségi statisztikák;
- az ESPHome által más OBIS-kódon várt mérőazonosító és meddőteljesítmény.

## Buffer

A bizonyított telegramhossz 1542 karakter. A konfiguráció mind az UART `rx_buffer_size`, mind a DSMR `max_telegram_length` értékét 1700 karakterre állítja. A két értéket későbbi hosszabb telegram esetén együtt kell emelni és újramérni.

Teljes minta: [`esphome/slimmelezer_demasz.yaml`](../esphome/slimmelezer_demasz.yaml).
