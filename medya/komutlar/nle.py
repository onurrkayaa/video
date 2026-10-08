"""medya nle <plan.json> [--bicim otio|kdenlive|edl|hepsi] [--muzik analiz/muzik.json] — kurgu planını
profesyonel kurgu programına aktarır: kullanıcı kurguyu orada elle sürdürsün (ince ayar, renk, ses).

  .otio           DaVinci Resolve (File > Import > Timeline…) — çok iz, erime, işaretler. Sınandı (Resolve 21.1,
                  2026-10-08, kare kodlu medya, testler/nle_olc.py): kesimler 0 kare, 12 karelik erime yerinde
                  (ağırlık rampasından 11,85 kare, ortası kesimde), 60 fps kaynak kare-kesin, 24 fps kaynakta ±1 kare
                  (Resolve giriş noktasını zaman çizelgesi ızgarasına aşağı yuvarlıyor), ses ≤ 2 ms (müzik çapraz
                  ilintiyle 0 ms). Resolve'da klip işaretleri ve kılavuzlar ölçülmedi.
  -kdenlive.otio  Kdenlive (File > OpenTimelineIO Import…) için uyarlanmış .otio. Kdenlive 26.08 içe aktarımının üç
                  hatası ölçüldü: (1) her izin SON klibi giriş noktasını kaybediyor (0'dan başlıyor) → her izin sonuna
                  1 karelik "SON — sil" klibi eklenir, içe aktardıktan sonra silinir; (2) erime uygulanamıyor ve
                  sonraki klibin giriş noktasını sıfırlıyor → erime yazılmaz: örtüşmenin ortasında kesim + işaret
                  (Kdenlive'da klibi seç, U); (3) klip işaretine kırpılmış başlangıcı yeniden ekliyor (kaydedilen
                  projede giriş 21 → işaret 42) → işaret klibin başına göreli yazılır (düzeltilmiş dosya Kdenlive'da
                  yeniden içe aktarılmadı). Ayrıca zaman çizelgesi hızı `duration().rate`'ten okunduğu için bütün
                  aralıklar zaman çizelgesi hızında yazılır (yoksa proje en yüksek kaynak hızında, ör. 60 fps açılıyor).
  .edl            CMX 3600 — yalnız görüntü izi (kesim + erime); bütün programlar açar
  (FCPXML yok: otio-fcpx-xml-adapter 1.0.0 geri okumada erimeyi düşürüp araya boşluk koydu, süre 10 → 12 sn — sınandı)

Plan: plan/kurgu.json (kurgu-zanaati biçimi). Çekimde `klip`/`klip_bas` (hazırlanmış ara klip: sdr, cfr,
yavaslat) varsa o, yoksa `kaynak`/`kaynak_bas` kullanılır; göreli yollar proje köküne (plan/..) göredir.
Zamanlar kare ızgarasına yuvarlanır. Plandaki erime bir örtüşmedir (sonraki çekim öncekinden önce başlar);
kurgu programlarının dili olan "kesim + iki yana taşan geçiş"e çevrilir. Aktarılamayanlar (kadraj, yakınlaştırma,
renk, özel geçişler, pişmemiş hız değişimi) klip notu + işaret olur ve uyarılır.

Bu dışa aktarım çizimin yerini tutmaz: teslim kompozisyondan çizilir; NLE dosyası elle devam etmek içindir.
Komut dosyayı OTIO ile geri okuyarak doğrular; programın içe aktarımını uçtan uca ölçmek için kare kodlu sınama
projesi: testler/nle_sinama.py (üret) + testler/nle_olc.py (programın çizimini plana karşı ölç).
Uyum (araştırma + şüpheci doğrulama, 2026-10-05): medya yolu DÜZ mutlak yol (Resolve 20.2 'file://' adresini
reddetti, Kdenlive çözmüyor); yolunda # % ? olan medya cikti/nle/medya/ altına güvenli adla bağlanır; işaret metni
'comment'a da yazılır (Kdenlive onu gösterir); EDL'de makara = kaynak dosya (A001…), ASCII ad, NON-DROP başlığı.
Çözünürlük OTIO'da taşınmaz: içe aktarırken zaman çizelgesi ayarını (en-boy, fps) kontrol et.
"""
from __future__ import annotations

import os
from pathlib import Path

from ..ortak import MedyaHatasi, bilgi, json_oku, oran, probe, ses_akisi, uyar, video_akisi

ORTUSEN = {"erime", "dissolve", "cross-dissolve", "crossfade"}
KESIM = {"", "kesim", "kesme", "cut", "j-kesim", "l-kesim"}
GORSEL = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}
NTSC = {23.976: 24000 / 1001, 29.97: 30000 / 1001, 47.952: 48000 / 1001, 59.94: 60000 / 1001,
        119.88: 120000 / 1001}
BICIMLER = {"otio": ("otio_json", ".otio"), "kdenlive": ("otio_json", "-kdenlive.otio"), "edl": ("cmx_3600", ".edl")}


TR_ASCII = str.maketrans("çğıİöşüÇĞÖŞÜâîûÂÎÛ—–’", "cgiIosuCGOSUaiuAIU--'")


def ascii_metin(m: str) -> str:
    """EDL yalnız ASCII taşır: Türkçe harfler ve uzun tire dönüştürülür, kalan ASCII dışı silinir."""
    return m.translate(TR_ASCII).encode("ascii", "ignore").decode()


def kare_hizi(fps: float) -> float:
    """23.976 gibi yuvarlanmış yazımları kesin NTSC oranına çevirir (kurgu programları kesin oran bekler)."""
    for yaklasik, kesin in NTSC.items():
        if abs(fps - yaklasik) < 0.01:
            return kesin
    return float(fps)


def _gecis(c: dict) -> tuple[str, int]:
    g = c.get("gecis") or {}
    if isinstance(g, str):
        g = {"tur": g}
    return str(g.get("tur") or "kesim").lower(), int(g.get("sure_kare") or 0)


class _Medya:
    """Kaynağın OTIO'ya gereken künyesi: kendi kare hızı, süresi, varsa başlangıç zaman kodu."""

    def __init__(self, yol: Path):
        self.yol = yol
        self.gorsel = yol.suffix.lower() in GORSEL
        self.fps = self.sure = self.tc = None
        self.ses = False
        if self.gorsel:
            return
        p = probe(yol)
        v = video_akisi(p)
        self.ses = ses_akisi(p) is not None
        self.fps = kare_hizi(oran(v.get("r_frame_rate"))) if v else None
        self.sure = float(p.get("format", {}).get("duration") or 0) or None
        for s in [p.get("format", {})] + p.get("streams", []):
            self.tc = self.tc or (s.get("tags") or {}).get("timecode")


def zaman_cizelgesi(plan: dict, kok: Path, muzik: dict | None = None, bas_tc: str = "00:00:00:00",
                    medya_klasoru: Path | None = None, kdenlive: bool = False):
    """Plan → OTIO Timeline. Dönüş: (timeline, uyarılar). medya_klasoru: yolunda # % ? olan medya buraya bağlanır.
    kdenlive: Kdenlive 26.08 içe aktarımına uyarlanmış zaman çizelgesi (modül belgesi: zaman çizelgesi hızı, erime yok,
    iz sonu "SON — sil" klibi)."""
    import opentimelineio as otio

    RT, TR = otio.opentime.RationalTime, otio.opentime.TimeRange
    fps = kare_hizi(float(plan["fps"]))
    uyarilar: list[str] = []
    onbellek: dict[Path, _Medya] = {}

    def medya(y: str) -> _Medya:
        p = Path(y).expanduser()
        p = (p if p.is_absolute() else kok / p).resolve()
        if not p.exists():
            raise MedyaHatasi(f"kaynak yok: {p}")
        if p not in onbellek:
            onbellek[p] = _Medya(p)
        return onbellek[p]

    def an(m: _Medya, sn: float):
        """Medyanın kendi saatinde bir an (kendi kare hızı + başlangıç zaman kodu). Kdenlive kipinde zaman çizelgesi
        hızında: Kdenlive başlangıcı bu hıza çevirip medyanın zaman kodunu da bu hızda okuyup çıkarıyor
        (src/otio/otioimport.cpp, 26.08), aynı hesapla yazınca kayma kalmaz."""
        h = fps if kdenlive else (m.fps or fps)
        t = RT(round(sn * h), h)
        if not m.tc:
            return t
        try:
            return otio.opentime.from_timecode(m.tc, h) + t
        except ValueError:                       # TC'nin kare alanı bu hızda yok (ör. 60 fps kamerada :45, 30 fps kurgu)
            uyarilar.append(f"Kdenlive: {m.yol.name} zaman kodu {m.tc} ({m.fps:g} fps) zaman çizelgesi hızında "
                            "okunamıyor — giriş noktası saniyeden yazıldı, Kdenlive'da denetle (sınanmadı)")
            return RT(round((otio.opentime.from_timecode(m.tc, m.fps or fps).to_seconds() + sn) * h), h)

    reller: dict[Path, str] = {}

    def guvenli_yol(p: Path) -> Path:
        if not any(c in str(p) for c in "#%?"):
            return p
        if medya_klasoru is None:
            uyarilar.append(f"yolda # % ? var, kurgu programı açamayabilir: {p}")
            return p
        medya_klasoru.mkdir(parents=True, exist_ok=True)
        hedef = medya_klasoru / "".join(c if c not in "#%?" else "_" for c in p.name)
        if not hedef.exists():
            try:
                os.link(p, hedef)                                     # aynı disk: hard link (yer kaplamaz)
            except OSError:
                hedef.symlink_to(p)
        uyarilar.append(f"yolunda # % ? olan medya güvenli adla bağlandı: {hedef.name}")
        return hedef

    def referans(m: _Medya):
        r = otio.schema.ExternalReference(target_url=str(guvenli_yol(m.yol)))   # düz mutlak yol (file:// değil)
        if m.sure:                                   # medyanın kendi aralığı: kendi hızında (Resolve bunu yazıyor)
            h = m.fps or fps
            bas = otio.opentime.from_timecode(m.tc, h) if m.tc else RT(0, h)
            r.available_range = TR(bas, RT(round(m.sure * h), h))
        return r

    def isaret(ad: str, kare_: int, renk) -> object:
        return otio.schema.Marker(name=ad, marked_range=TR(RT(kare_, fps), RT(0, fps)), color=renk, comment=ad)

    C = sorted(plan.get("cekimler") or [], key=lambda c: c["cikti_bas"])
    if not C:
        raise MedyaHatasi("planda çekim yok")

    # 1) her çekim: zaman çizelgesi kareleri [bas, son) ve klibin kendi saatinde başlangıcı
    P = []
    for i, c in enumerate(C):
        no = c.get("no", i + 1)
        hazir = bool(c.get("klip")) and c.get("klip") != c.get("kaynak")
        m = medya(c["klip"] if hazir else c["kaynak"])
        hiz = float(c.get("hiz", 1.0))
        x = {"c": c, "no": no, "m": m, "bas": round(c["cikti_bas"] * fps), "son": round(c["cikti_son"] * fps),
             "k_bas": float(c.get("klip_bas", 0.0) if hazir else c.get("kaynak_bas", 0.0)), "notlar": []}
        if x["son"] <= x["bas"]:
            raise MedyaHatasi(f"çekim {no}: süre ≤ 0 kare")
        if abs(hiz - 1) > 1e-9 and not (hazir and hiz < 1):
            x["notlar"].append(f"hız {hiz:g}x — kurgu programında elle uygula (1x aktarıldı)")
            uyarilar.append(f"çekim {no}: pişmemiş hız değişimi ({hiz:g}x) 1x aktarıldı + işaret "
                            "(ağır çekimi medya yavaslat ile önceden üret)")
        for alan in ("kadraj", "hareket"):
            if c.get(alan):
                x["notlar"].append(f"{alan}: {c[alan]}")
        P.append(x)
    if any(x["notlar"] and any(n.startswith(("kadraj", "hareket")) for n in x["notlar"]) for x in P):
        uyarilar.append("kadraj/yakınlaştırma aktarılamaz (standart karşılığı yok): klip notu + işaret olarak taşındı")

    # 2) erime: plandaki örtüşmeyi "kesim noktası + iki yana taşan geçiş"e çevir
    gecisler: dict[int, tuple[int, int]] = {}
    for i in range(1, len(P)):
        a, b = P[i - 1], P[i]
        tur, n = _gecis(b["c"])
        ortusme = a["son"] - b["bas"]
        if tur in ORTUSEN:
            L = ortusme if ortusme > 0 else n
            if L <= 0:
                uyarilar.append(f"çekim {b['no']}: erime var ama süresi yok (gecis.sure_kare) → kesim yazıldı")
                continue
            k = L // 2
            if ortusme > 0:                              # örtüşmenin ortasında kes; taşan kısımlar tutamak olur
                kesim = b["bas"] + k
                b["k_bas"] += (kesim - b["bas"]) / fps
                a["son"], b["bas"] = kesim, kesim
            else:                                        # örtüşme yok: geçiş kaynakların fazladan karesini ister
                eksik = []
                if b["k_bas"] - k / fps < -1e-9:
                    eksik.append(f"{b['no']} başında {k} kare")
                a_son_kaynak = a["k_bas"] + (a["son"] - a["bas"] + L - k) / fps
                if a["m"].sure and a_son_kaynak > a["m"].sure + 1e-6:
                    eksik.append(f"{a['no']} sonunda {L - k} kare")
                if eksik:
                    uyarilar.append(f"çekim {b['no']}: erime için kaynakta yeterli fazla kare yok ({', '.join(eksik)})"
                                    " — kurgu programı erimeyi kısaltabilir")
            gecisler[i] = (k, L - k)
        elif ortusme > 0:
            raise MedyaHatasi(f"çekim {b['no']}: önceki çekimle {ortusme} kare örtüşüyor ama geçiş '{tur}' "
                              "(yalnız erime örtüşür)")
        elif tur not in KESIM:
            b["notlar"].append(f"geçiş: {tur} (kompozisyonda çizilir)")
            uyarilar.append(f"çekim {b['no']}: '{tur}' geçişi aktarılamaz → kesim + işaret")

    # 3) görüntü izi
    V = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    imlec = 0
    for i, x in enumerate(P):
        if x["bas"] > imlec:
            V.append(otio.schema.Gap(source_range=TR(RT(0, fps), RT(x["bas"] - imlec, fps))))
        if i in gecisler and not kdenlive:
            gi, go = gecisler[i]
            V.append(otio.schema.Transition(name="erime", transition_type=otio.schema.TransitionTypes.SMPTE_Dissolve,
                                            in_offset=RT(gi, fps), out_offset=RT(go, fps)))
        elif i in gecisler:
            L = sum(gecisler[i])
            x["notlar"].insert(0, f"erime {L} kare buraya: Kdenlive'da klibi seç, U (ya da birleşime çift tıkla), "
                                  f"süreyi {L} kare yap")
        m, sure = x["m"], x["son"] - x["bas"]
        h = fps if kdenlive else (m.fps or fps)
        kaynak = TR(an(m, x["k_bas"]) if not m.gorsel else RT(0, fps), RT(round(sure / fps * h), h))
        klip = otio.schema.Clip(name=f"{x['no']:02d} {m.yol.name}" if isinstance(x["no"], int) else str(x["no"]),
                                media_reference=referans(m), source_range=kaynak)
        klip.metadata["medya"] = {k: v for k, v in x["c"].items() if isinstance(v, (str, int, float, bool, dict, list))}
        klip.metadata["cmx_3600"] = {"reel": reller.setdefault(m.yol, f"A{len(reller) + 1:03d}")}   # makara = kaynak
        if x["notlar"]:
            notu = " · ".join(x["notlar"])
            # klibin ilk karesine. OTIO'da işaret klibin kaynak saatindedir; Kdenlive 26.08 kırpılmış başlangıcı yeniden
            # ekliyor (otioimport.cpp: pos = start + işaret; kaydedilen projede giriş 21 → işaret 42, ölçüldü 2026-10-08)
            # → Kdenlive kipinde göreli yazılır, Kdenlive'ın kaydırmada düştüğü medya zaman kodu da düşülür.
            bas_i = RT(0, h) - an(m, 0) if kdenlive else kaynak.start_time
            klip.markers.append(otio.schema.Marker(name=notu, comment=notu, marked_range=TR(bas_i, RT(0, h)),
                                                   color=otio.schema.MarkerColor.RED))
        V.append(klip)
        imlec = x["son"]
    toplam = imlec

    izler, iz_medya = [V], [P[-1]["m"]]
    # 4) müzik izi: müzik dosyasının `bas` anı zaman çizelgesinin 0'ına denk gelir
    mz = plan.get("muzik") or {}
    if mz.get("dosya"):
        m = medya(mz["dosya"])
        bas = float(mz.get("bas", 0.0))
        sure = toplam if not m.sure else min(toplam, round((m.sure - bas) * fps))
        A = otio.schema.Track(name="A1 müzik", kind=otio.schema.TrackKind.Audio)
        A.append(otio.schema.Clip(name=m.yol.name, media_reference=referans(m),
                                  source_range=TR(RT(round(bas * fps), fps), RT(sure, fps))))
        izler.append(A)
        iz_medya.append(m)
        if sure < toplam:
            uyarilar.append(f"müzik {toplam - sure} kare erken bitiyor")
    # 5) çekim sesi izleri: ses = kendi olanlar asıl kaynaktan; örtüşen sesler ayrı ize (elle çapraz geçiş için)
    ses_izleri: list[list] = []
    for x in P:
        c = x["c"]
        if c.get("ses") != "kendi":
            continue
        m = medya(c["kaynak"])
        if not m.ses:
            uyarilar.append(f"çekim {x['no']}: ses 'kendi' ama kaynakta ses yok")
            continue
        b0, s0 = round(c["cikti_bas"] * fps), round(c["cikti_son"] * fps)
        iz = next((z for z in ses_izleri if z[-1][1] <= b0), None)
        if iz is None:
            iz = []
            ses_izleri.append(iz)
        iz.append((b0, s0, m, float(c.get("kaynak_bas", 0.0)), x["no"]))
    for j, iz in enumerate(ses_izleri):
        A = otio.schema.Track(name=f"A{j + 2} çekim sesi", kind=otio.schema.TrackKind.Audio)
        imlec = 0
        for b0, s0, m, kb, no in iz:
            if b0 > imlec:
                A.append(otio.schema.Gap(source_range=TR(RT(0, fps), RT(b0 - imlec, fps))))
            h = fps if kdenlive else (m.fps or fps)
            A.append(otio.schema.Clip(name=f"{no} ses", media_reference=referans(m),
                                      source_range=TR(an(m, kb), RT(round((s0 - b0) / fps * h), h))))
            imlec = s0
        izler.append(A)
        iz_medya.append(iz[-1][2])

    if kdenlive:                                     # iz sonu düzeltmesi: son klibin giriş noktası kaybolmasın
        for iz, m in zip(izler, iz_medya):
            uzunluk = round(iz.duration().rescaled_to(fps).value)
            if uzunluk < toplam:
                iz.append(otio.schema.Gap(source_range=TR(RT(0, fps), RT(toplam - uzunluk, fps))))
            bas0 = an(m, 0) if not m.gorsel else RT(0, fps)          # kaydırma 0: düzeltme klibi kendisi bozulmaz
            iz.append(otio.schema.Clip(name="SON — sil", media_reference=referans(m), source_range=TR(bas0, RT(1, fps))))
            # (işaret konmaz: Kdenlive klip işaretini kutudaki klibe yazar, aynı medyanın her örneğinde görünür)
        if gecisler:
            uyarilar.append(f"Kdenlive: {len(gecisler)} erime kesim + işaret olarak yazıldı (Kdenlive 26.08 OTIO'dan "
                            "erime uygulayamıyor, sonraki klibi kaydırıyor — ölçüldü): işaretlerde klibi seç, U")
        uyarilar.append("Kdenlive: her izin sonunda 1 karelik 'SON — sil' klibi var — içe aktardıktan sonra sil "
                        "(yoksa son klibin giriş noktası kayboluyor — ölçüldü)")
    tl = otio.schema.Timeline(name=plan.get("ad") or kok.name, global_start_time=otio.opentime.from_timecode(bas_tc, fps))
    tl.tracks.extend(izler)
    # 6) ölçü başı işaretleri (müzik analizi verildiyse): kurgu programında vuruşa elle kesmek için
    if muzik and mz.get("dosya"):
        bas = float(mz.get("bas", 0.0))
        for t in muzik.get("olcu_baslari") or []:
            k = round((t - bas) * fps)
            if 0 <= k < toplam:
                tl.tracks.markers.append(isaret("ölçü başı", k, otio.schema.MarkerColor.YELLOW))
        if muzik.get("guven_seviye") != "yuksek":
            uyarilar.append(f"müzik güveni '{muzik.get('guven_seviye')}': ölçü başı işaretleri yaklaşık, vuruş iddiası yok")
    return tl, uyarilar


def _dogrula(yol: Path, ad: str, beklenen_kare: int, fps: float) -> str:
    """Yazılan dosyayı OTIO ile geri okur: süre ve klip sayısı tutuyor mu (içe aktarmanın vekili)."""
    import opentimelineio as otio

    kw = {"rate": fps} if ad == "cmx_3600" else {}
    tl = otio.adapters.read_from_file(str(yol), adapter_name=ad, **kw)
    v = next((t for t in tl.tracks if t.kind == otio.schema.TrackKind.Video), None)
    if v is None:
        raise MedyaHatasi(f"{yol.name}: geri okunurken görüntü izi yok")
    sure = round(v.duration().rescaled_to(fps).value)
    klip = sum(1 for _ in v.find_clips())
    gecis = sum(1 for c in v if isinstance(c, otio.schema.Transition))
    if abs(sure - beklenen_kare) > 1:
        raise MedyaHatasi(f"{yol.name}: geri okunan süre {sure} kare, beklenen {beklenen_kare}")
    return f"{klip} klip, {gecis} geçiş, {sure} kare"


def nle_(args) -> int:
    import opentimelineio as otio

    plan_yolu = Path(args.plan).resolve()
    plan = json_oku(plan_yolu)
    kok = Path(args.kok).resolve() if args.kok else plan_yolu.parent.parent
    muzik_yolu = args.muzik or (plan.get("muzik") or {}).get("analiz")
    muzik = None
    if muzik_yolu:
        my = Path(muzik_yolu)
        muzik = json_oku(my if my.is_absolute() else kok / my)
    cikti = Path(args.cikti) if args.cikti else kok / "cikti" / "nle" / plan_yolu.stem
    tl, uyarilar = zaman_cizelgesi(plan, kok, muzik, args.bas_zaman_kodu, medya_klasoru=cikti.parent / "medya")
    fps = kare_hizi(float(plan["fps"]))
    beklenen = round(tl.tracks[0].duration().rescaled_to(fps).value)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    bicimler = list(BICIMLER) if args.bicim == "hepsi" else [args.bicim]
    for b in bicimler:
        ad, uzanti = BICIMLER[b]
        hedef = cikti.with_name(cikti.name + uzanti) if uzanti.startswith("-") else cikti.with_suffix(uzanti)
        if b == "kdenlive":
            tl_k, uy_k = zaman_cizelgesi(plan, kok, muzik, args.bas_zaman_kodu, medya_klasoru=cikti.parent / "medya",
                                         kdenlive=True)
            otio.adapters.write_to_file(tl_k, str(hedef), adapter_name=ad)
            uyarilar += [u for u in uy_k if u.startswith("Kdenlive")]
            print(f"✓ {hedef}  ({_dogrula(hedef, ad, beklenen, fps)}; zaman çizelgesi hızı "
                  f"{otio.adapters.read_from_file(str(hedef)).duration().rate:g})")
            continue
        if b == "edl":                                   # EDL tek görüntü izi taşır; yalnız ASCII
            yalniz = otio.schema.Timeline(name=ascii_metin(tl.name), global_start_time=tl.global_start_time)
            iz = tl.tracks[0].deepcopy()
            for c in iz.find_clips():
                c.name = ascii_metin(c.name)
                for mk in c.markers:
                    mk.name = mk.comment = ascii_metin(mk.name)
            yalniz.tracks.append(iz)
            otio.adapters.write_to_file(yalniz, str(hedef), adapter_name=ad, rate=fps, style="avid")
            satirlar = hedef.read_text().splitlines()      # uyarlayıcı FCM yazmıyor, NTSC'de ';' (düşen kare) yazıyor
            satirlar = [satirlar[0], "FCM: NON-DROP FRAME"] + [
                l if l.startswith("*") else l.replace(";", ":") for l in satirlar[1:]]
            hedef.write_text("\n".join(satirlar) + "\n")
        else:
            otio.adapters.write_to_file(tl, str(hedef), adapter_name=ad)
        print(f"✓ {hedef}  ({_dogrula(hedef, ad, beklenen, fps)})")
    for u in dict.fromkeys(uyarilar):                # aynı uyarı birden çok klipten gelebilir
        uyar(u)
    bilgi("Resolve: File > Import > Timeline… → .otio; açılan pencerede 'Set timeline resolution' "
          f"{plan.get('boyut') or '?'} ve kare hızı {plan['fps']} olsun (OTIO çözünürlük taşımaz). Kdenlive: "
          "File > OpenTimelineIO Import… → -kdenlive.otio (çözünürlüğü ilk klipten alır), sonra 'SON — sil' "
          "kliplerini sil. Medya yolları mutlak; dosyaları taşırsan yeniden bağla.")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="kurgu planını kurgu programına aktarır (.otio / -kdenlive.otio / .edl)",
                       description=__doc__.split("\n\n")[0])
    p.add_argument("plan", help="plan/kurgu.json")
    p.add_argument("--bicim", default="otio", choices=[*BICIMLER, "hepsi"])
    p.add_argument("--muzik", help="medya muzik JSON'u: ölçü başı işaretleri (varsayılan plan.muzik.analiz)")
    p.add_argument("--kok", help="göreli yolların kökü (varsayılan: planın iki üstü = proje klasörü)")
    p.add_argument("--bas-zaman-kodu", default="00:00:00:00",
                   help="zaman çizelgesi başlangıcı (.otio'ya yazılır; EDL uyarlayıcısı her zaman 00:00:00:00 yazar)")
    p.add_argument("--cikti", help="uzantısız çıktı yolu (varsayılan: cikti/nle/<plan adı>)")
    p.set_defaults(islev=nle_)
