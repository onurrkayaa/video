"""Bir komutu çalıştırıp 0,2 sn'de bir örnekler: boş disk (en düşük), süreç ağacının toplam RSS'i (en yüksek), takas.
  python olcer.py <sonuc.json> -- <komut …>"""
import json, re, shutil, subprocess, sys, time
cikti, komut = sys.argv[1], sys.argv[sys.argv.index("--") + 1:]
def takas():
    m = re.search(r"used = ([\d.]+)M", subprocess.run(["sysctl", "vm.swapusage"], capture_output=True, text=True).stdout)
    return float(m.group(1)) if m else None
def agac_rss(kok):
    satir = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True).stdout.split("\n")
    c, r = {}, {}
    for s in satir:
        p = s.split()
        if len(p) == 3:
            c.setdefault(int(p[1]), []).append(int(p[0])); r[int(p[0])] = int(p[2])
    top, yigin = 0, [kok]
    while yigin:
        x = yigin.pop(); top += r.get(x, 0); yigin += c.get(x, [])
    return top * 1024
bos0, takas0 = shutil.disk_usage("/").free, takas()
t0 = time.monotonic()
p = subprocess.Popen(komut)
en_dusuk, en_rss, en_takas = bos0, 0, takas0 or 0
import os, signal
TAKAS_SINIR = float(os.environ.get("OLCER_TAKAS_MB", "1e9")); DISK_SINIR = float(os.environ.get("OLCER_BOS_GB", "0")) * 1e9
durduruldu = None
def agac(kok):
    satir = subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True).stdout.split("\n")
    c = {}
    for s_ in satir:
        q = s_.split()
        if len(q) == 2: c.setdefault(int(q[1]), []).append(int(q[0]))
    out, y = [], [kok]
    while y:
        x = y.pop(); out.append(x); y += c.get(x, [])
    return out
while p.poll() is None:
    en_dusuk = min(en_dusuk, shutil.disk_usage("/").free)
    en_rss = max(en_rss, agac_rss(p.pid))
    t = takas(); en_takas = max(en_takas, t or 0)
    if (t or 0) > TAKAS_SINIR or shutil.disk_usage("/").free < DISK_SINIR:
        durduruldu = f"takas {t} MB / boş {shutil.disk_usage('/').free / 1e9:.1f} GB sınırı aştı"
        for x in reversed(agac(p.pid)):
            try: os.kill(x, signal.SIGKILL)
            except ProcessLookupError: pass
        break
    time.sleep(0.2)
p.wait()
sure = time.monotonic() - t0
son = shutil.disk_usage("/").free
r = {"komut": komut, "cikis": p.returncode, "sure_sn": round(sure, 2), "disk_tepe_gb": round((bos0 - en_dusuk) / 1e9, 3),
     "disk_kalici_gb": round((bos0 - son) / 1e9, 3), "rss_tepe_gb": round(en_rss / 1e9, 3), "takas_once_mb": takas0,
     "takas_tepe_mb": en_takas, "takas_sonra_mb": takas(), "durduruldu": durduruldu}
json.dump(r, open(cikti, "w"), indent=1)
print(json.dumps({k: v for k, v in r.items() if k != "komut"}))
sys.exit(p.returncode)
