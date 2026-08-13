# A korábbi statikus REST package kivezetve

A korábbi `slimmelezer_demasz.yaml` package 31 rögzített REST-szenzort hozott létre, de új OBIS-regisztert nem tudott automatikusan felvenni. Emiatt az új, dinamikus `custom_components/slimmelezer_demasz` integráció váltotta fel.

Ne telepítsd egyszerre a régi REST package-et és az egyedi integrációt, mert a 31 ismert nyers adatból párhuzamos, duplikált entitások készülnének.
