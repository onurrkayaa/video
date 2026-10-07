import sys, json
alan = ['klip','N','yontem','ara_kare','psnr_y_ort','psnr_y_kotu5_ort','psnr_y_min','ssim_y_ort','ssim_y_kotu5_ort','tavan_ozgun_psnr_y','hizalama','sure_sn','ms_ara_kare']
for l in sys.stdin:
    try:
        d = json.loads(l); print(' | '.join(f"{d.get(k)}" for k in alan))
    except Exception:
        print(l.rstrip()[:400])
