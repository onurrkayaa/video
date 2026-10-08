"""Komutu çalıştırır; süreç ağacının toplam RSS'inin en yüksek olduğu andaki süreç başı RSS dağılımını yazar."""
import subprocess, sys, time
komut = sys.argv[sys.argv.index("--") + 1:]
p = subprocess.Popen(komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
en, an = 0, None
def tur(c):
    if "perspective" in c: return "geometri"
    if "-copyts" in c: return "çözücü"
    if "libx264" in c: return "kodlayıcı"
    if "python" in c: return "python"
    return c[:30]
while p.poll() is None:
    s = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss=,command="], capture_output=True, text=True).stdout.splitlines()
    ch, rss, cmd = {}, {}, {}
    for l in s:
        q = l.split(None, 3)
        if len(q) == 4:
            ch.setdefault(int(q[1]), []).append(int(q[0])); rss[int(q[0])] = int(q[2]); cmd[int(q[0])] = q[3]
    agac, y = [], [p.pid]
    while y:
        x = y.pop(); agac.append(x); y += ch.get(x, [])
    top = sum(rss.get(x, 0) for x in agac)
    if top > en:
        en, an = top, sorted(((tur(cmd.get(x, "")), rss.get(x, 0) // 1024) for x in agac), key=lambda t: -t[1])
    time.sleep(0.1)
print(f"tepe {en / 1e6:.2f} GB:", an)
