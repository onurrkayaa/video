"""`medya` komutu: stüdyonun tek giriş noktası.

Her komut medya/komutlar/<modül>.py içinde `kaydet(alt)` ile tanımlanır ve yalnız çağrıldığında yüklenir;
böylece ağır bir aracın eksikliği diğer komutları bozmaz.
"""
from __future__ import annotations

import argparse
import importlib
import sys

from .ortak import MedyaHatasi

# komut adı -> (modül, kısa açıklama). Sıra yardım çıktısındaki sıradır.
KOMUTLAR = {
    # sistem
    "yetenekler": ("sistem", "yetenekleri, sağlayıcıları ve kurulu olup olmadıklarını listeler"),
    "kur": ("sistem", "bir sağlayıcıyı kurar (lisans ve boyutu gösterir)"),
    "test": ("sistem", "yeteneklerin duman testlerini çalıştırır"),
    "proje": ("proje", "yeni üretim klasörü açar (projeler/YYYY-AA-GG-ad)"),
    # inceleme ve analiz
    "incele": ("incele", "dosya künyesi: süre, fps (CFR/VFR), döndürme, HDR, ses, GPS + uyarılar"),
    "kontak": ("kontak", "zaman damgalı temas sayfası (kare ızgarası) üretir"),
    "sahneler": ("sahneler", "çekim sınırlarını bulur"),
    "ses-turu": ("ses_turu", "ses yalnız müzik mi, çekim sesi karışık mı — ölçer"),
    "muzik": ("muzik", "vuruş, ölçü başı, bölüm + güven skoru (iki yöntemle sınanır)"),
    "yaziya-dok": ("yaziya_dok", "konuşmayı kelime zamanlarıyla yazıya döker (Whisper, yerel)"),
    "analiz": ("analiz", "kare kare görüntü analizi: estetik, yüz kalitesi, ilgi alanı, etiket (Apple Vision)"),
    "ses-olay": ("ses_olay", "ses olayları: kahkaha, alkış, konuşma, şarkı, müzik (Apple SoundAnalysis)"),
    # dönüştürme
    "sdr": ("donustur", "HDR (HLG/PQ) çekimi doğru ton eşlemeyle SDR bt709'a çevirir"),
    "cfr": ("donustur", "değişken kare hızını sabit kare hızına çevirir"),
    "meta-temizle": ("donustur", "konum/GPS ve kişisel üst veriyi siler"),
    "yavaslat": ("yavaslat", "ağır çekim: doğal (yüksek fps) / Apple ML ara kare / ffmpeg"),
    "ayir": ("ayir", "sesi katmanlara ayırır: vokal, davul, bas, diğer (Demucs)"),
    "gorsel-uret": ("gorsel_uret", "metinden ya da referans görselden görsel üretir (FLUX.2 klein 4B, yerel)"),
    "arkaplan-sil": ("arkaplan", "arka planı siler, şeffaf PNG (Apple Vision)"),
    # ses ve teslim
    "seslendir": ("seslendir", "metinden dış ses (Türkçe dahil): tutarlı ses kimliği, Whisper/ECAPA doğrulamalı"),
    "ses-temizle": ("ses_temizle", "konuşmadaki gürültüyü azaltır: rüzgâr, kalabalık, uğultu (DeepFilterNet3)"),
    "ustala": ("ustala", "ses düzeyini hedefe getirir (LUFS + gerçek tepe), görüntüye dokunmaz"),
    "senkron": ("senkron", "kesimlerin vuruşa uzaklığını ölçer"),
    "denetle": ("denetle", "teslim öncesi kalite denetimi: siyah/donma/flaş kare, ses, senkron, üst veri"),
    "nle": ("nle", "kurgu planını kurgu programına aktarır: DaVinci Resolve, Kdenlive (.otio), EDL"),
    "zamankodu": ("zamankodu", "gözden geçirme taslağı: köşede dk:sn.kare (geri bildirim için; teslim değil)"),
    "temizle": ("temizle", "disk bütçesi: yeniden üretilebilir önbellekleri raporla/temizle"),
}


def ana(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ayr = argparse.ArgumentParser(prog="medya", description="Yerel medya stüdyosu — yetenek katmanı.",
                                  formatter_class=argparse.RawDescriptionHelpFormatter,
                                  epilog="\n".join(f"  {k:<14} {v[1]}" for k, v in KOMUTLAR.items()))
    alt = ayr.add_subparsers(dest="komut", metavar="komut")
    # yalnız çağrılan komutun modülünü yükle (yardım için hepsinin adı epilog'da)
    istenen = next((a for a in argv if not a.startswith("-")), None)
    yuklenecek = [istenen] if istenen in KOMUTLAR else []
    for ad in yuklenecek:
        modul = importlib.import_module(f".komutlar.{KOMUTLAR[ad][0]}", __package__)
        modul.kaydet(alt, ad)
    if not yuklenecek:
        ayr.print_help()
        return 0 if not argv or istenen is None else 2
    args = ayr.parse_args(argv)
    try:
        return int(args.islev(args) or 0)
    except MedyaHatasi as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(ana())
