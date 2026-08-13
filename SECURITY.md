# Biztonsági hibák bejelentése

Biztonsági problémát ne nyilvános hibajegyben jelents. A GitHub repository **Security → Report a vulnerability** felületén küldj privát bejelentést.

Ne csatolj Home Assistant tokent, Wi-Fi-jelszót, teljes raw telegramot, mérőazonosítót vagy belső hálózati címet.

A projekt alapműködésben kizárólag helyi HTTP-végpontot olvas. A végpontot ne tedd elérhetővé az internetről, és ne használj hozzá nyilvános porttovábbítást.

Az ismeretlen OBIS-kódok automatikus GitHub-jelentése külön bekapcsolható külső adatkapcsolat. Csak a célrepositoryra korlátozott finomhangolt tokent használj, kizárólag `Issues: write` jogosultsággal. A jelentés kódja nem továbbít mérési értéket, mérőazonosítót, raw telegramot vagy belső hálózati címet. A token nem kerül a diagnosztikába, de a Home Assistant biztonsági mentésében szerepelhet; a mentést ennek megfelelően védd.
