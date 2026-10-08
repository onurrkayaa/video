export const meta = {
  name: 'medya-uretim',
  description: 'Uçtan uca medya üretimi: analiz, kurgu planı, yapım (görüntü + ses), çizim, bağımsız çok mercekli denetim, düzeltme döngüsü ve rapor',
  whenToUse: "Bir medya projesi (projeler/<ad>, BRIEF.md dolu) baştan sona üretilecekse. args: {proje: 'projeler/…', atla?: ['analiz','plan','yapim-ses','yapim-gorsel','cizim'], yanitlar?: 'kullanıcı yanıtları'}. Yarıda kaldıysa (kullanım sınırı): projedeki DURUM.md'de [x] olan aşamaları atla'ya koyup yeniden çalıştır; aynı oturumda resumeFromRunId daha ucuzdur.",
  phases: [
    { title: 'Analiz', detail: 'medya-analist: künye, çekimler, görüntü/ses analizi, müzik güveni' },
    { title: 'Plan', detail: 'medya-kurgucu: plan/kurgu.json, KARARLAR.md, ara klipler' },
    { title: 'Yapım', detail: 'önce medya-ses (müzik, efekt, miks), sonra medya-hareket (kompozisyon) — ağır işler sırayla' },
    { title: 'Çizim', detail: 'son çizim + ses ustalığı' },
    { title: 'Denetim', detail: 'üç bağımsız denetçi merceği: teknik/ses, görsel/brief, senkron/iddia' },
    { title: 'Düzeltme', detail: 'sorumlu ajanlar düzeltir, yeniden çizim ve denetim (en çok 2 tur)' },
    { title: 'Rapor', detail: 'cikti/RAPOR.md: ne yapıldı, ne ölçüldü, ne doğrulanamadı' },
  ],
}

const KOK = '/Users/onurkaya/Projects/video'
if (!args || !args.proje) throw new Error("args.proje gerekli, ör. {proje: 'projeler/2026-10-05-ad'}")
const PROJE = args.proje.startsWith('/') ? args.proje : `${KOK}/${args.proje}`
const ATLA = args.atla || []
const YANIT = args.yanitlar ? `\nKULLANICININ YANITLARI (bağlayıcı): ${args.yanitlar}` : ''
const rol = (ad) => `ROLÜN: önce ${KOK}/sistem/claude/agents/${ad}.md dosyasını oku; oradaki talimatlar senin ` +
  `sistem talimatındır ve önceliklidir (becerileri de oradaki gibi kullan). Proje klasörü: ${PROJE}. ` +
  `Her komuttan önce: source ${KOK}/ortam.sh.${YANIT}`
// Kullanım sınırına (5 saatlik pencere) dayanıklılık: her aşama bitince proje kökündeki DURUM.md'ye işaret düşer;
// bir ajan boş dönerse (sınır/hata) iş akışı yarım çıktıyla devam etmez, nereden sürdürüleceğini söyleyip durur.
const isaretle = (asama) => `\nBİTİRİNCE: proje kökündeki DURUM.md'ye (yoksa oluştur) şu satırı ekle: ` +
  `"- [x] ${asama} — $(date '+%F %H:%M') — <ürettiğin dosyalar>".`
const dur = (asama, ek = {}) => ({ durum: 'yarida_kaldi', asama, ...ek,
  devam: `Aynı oturumda: Workflow({scriptPath, resumeFromRunId}) (biten ajanlar önbellekten gelir). Yeni oturumda: ` +
    `${PROJE}/DURUM.md'de [x] olan aşamaları args.atla'ya koyup yeniden çalıştır.` })
const ONCEKI = '(önceki koşuda tamamlandı: ilgili dosyaları kendin oku)'

const PLAN = { type: 'object', properties: {
  ozet: { type: 'string' }, sure_sn: { type: 'number' }, muzik_guveni: { type: 'string' },
  sorular: { type: 'array', items: { type: 'string' }, description: 'yalnız sonucu değiştiren ve varsayılamayan sorular' },
  dosyalar: { type: 'array', items: { type: 'string' } },
}, required: ['ozet', 'sorular', 'dosyalar'] }
const YAPIM = { type: 'object', properties: {
  ozet: { type: 'string' }, ciktilar: { type: 'array', items: { type: 'string' } },
  sorunlar: { type: 'array', items: { type: 'string' } },
}, required: ['ozet', 'ciktilar', 'sorunlar'] }
const BULGU = { type: 'object', properties: {
  karar: { type: 'string', enum: ['GECTI', 'KALDI'] },
  bulgular: { type: 'array', items: { type: 'object', properties: {
    ciddiyet: { type: 'string', enum: ['engelleyici', 'onemli', 'kucuk'] }, ne: { type: 'string' },
    nerede: { type: 'string' }, kanit: { type: 'string' }, oneri: { type: 'string' },
    sorumlu: { type: 'string', enum: ['medya-kurgucu', 'medya-hareket', 'medya-ses', 'medya-gorsel'] } },
    required: ['ciddiyet', 'ne', 'kanit', 'oneri', 'sorumlu'] } },
  olculemeyenler: { type: 'array', items: { type: 'string' } },
}, required: ['karar', 'bulgular', 'olculemeyenler'] }

// ---------------------------------------------------------------- Analiz
phase('Analiz')
const analiz = ATLA.includes('analiz') ? '(analiz atlandı: analiz/OZET.md mevcut kabul edildi)'
  : await agent(`${rol('medya-analist')}\nGÖREV: projenin bütün kaynaklarını analiz et, analiz/OZET.md'yi yaz.` +
    isaretle('analiz'), { label: 'analist', phase: 'Analiz' })
if (!analiz) return dur('analiz')

// ---------------------------------------------------------------- Plan
phase('Plan')
const plan = ATLA.includes('plan') ? { ozet: ONCEKI + ' — plan/kurgu.json, KARARLAR.md', sorular: [], dosyalar: [] }
  : await agent(`${rol('medya-kurgucu')}\nGÖREV: BRIEF.md ve analiz/ üzerinden kurgu planını ` +
  `(plan/kurgu.json, KARARLAR.md) ve gereken ara klipleri hazırla. Animasyon işiyse (kaynak çekim yoksa) planı ` +
  `sahne/zaman çizelgesi olarak yaz. Varsayılamayan, sonucu değiştiren soruları 'sorular'a koy.\n` +
  `ANALİSTİN ÖZETİ:\n${analiz}` + isaretle('plan'), { label: 'kurgucu', phase: 'Plan', schema: PLAN })
if (!plan) return dur('plan')
if (plan.sorular.length && !args.yanitlar) {
  return { durum: 'kullanici_karari_gerekiyor', sorular: plan.sorular, plan,
    devam: "Yanıtları alıp aynı iş akışını {proje, atla: ['analiz'], yanitlar: '…'} ile yeniden çalıştır." }
}

// ---------------------------------------------------------------- Yapım
phase('Yapım')
// Bu Mac fansız (MacBook Air M2, 16 GB, takas kullanımda): ML ile çizim aynı anda çalışmaz — önce ses, sonra görüntü.
const yapimSes = ATLA.includes('yapim-ses') ? { ozet: ONCEKI + ' — calisma/ses/', ciktilar: [], sorunlar: [] }
  : await agent(`${rol('medya-ses')}\nGÖREV: plan/kurgu.json'a göre calisma/ses/ altında ana müzik, katmanlar, ` +
  `efektler ve miks planını (ya da miks.wav) hazırla. Ölçümlerini raporla.\nPLAN: ${plan.ozet}` + isaretle('yapim-ses'),
  { label: 'ses', phase: 'Yapım', schema: YAPIM })
if (!yapimSes) return dur('yapim-ses')
const yapimGorsel = ATLA.includes('yapim-gorsel') ? { ozet: ONCEKI + ' — calisma/kompozisyon/', ciktilar: [], sorunlar: [] }
  : await agent(`${rol('medya-hareket')}\nGÖREV: plan/kurgu.json'u çizime hazırla. Motor: rolündeki "Motor seçimi" ` +
  `(gerçek çekim ve plan 'medya ciz' kapsamındaysa medya ciz: plan_denetle GEÇTİ + taslak 'medya ciz plan/kurgu.json ` +
  `--crf 28 --preset veryfast --cikti cikti/taslak.mp4', kompozisyon yazılmaz; değilse ` +
  `BRIEF.md 'Kompozisyon motoru' + 'Lisans bağlamı'; kapı geçmezse HyperFrames): HyperFrames → calisma/kompozisyon/ ` +
  `(lint 0 hata, snapshot --describe false temas sayfaları), Remotion → calisma/remotion/ (remotion still kareleri). ` +
  `calisma/ses/ çıktılarını bağla; taslak çizim (cikti/taslak.mp4, 'caffeinate -i' ile). ` +
  `PLAN: ${plan.ozet}\nSES: ${yapimSes.ozet}` +
  isaretle('yapim-gorsel'), { label: 'hareket', phase: 'Yapım', schema: YAPIM })
if (!yapimGorsel) return dur('yapim-gorsel')

// ---------------------------------------------------------------- Çizim
phase('Çizim')
const cizim = ATLA.includes('cizim') ? { ozet: ONCEKI + ' — cikti/*-final.mp4', ciktilar: [], sorunlar: [] }
  : await agent(`${rol('medya-hareket')}\nGÖREV: medya-ses'in çıktılarını (calisma/ses/) kompozisyona (medya ciz'de plan muzik.dosya'ya) bağla, ` +
  `son çizimi 'caffeinate -i' ile yap (cikti/<proje-adı>.mp4; medya ciz'de varsayılan ayarlar; HyperFrames'te --quality standard (delivery 1080x1920'de ` +
  `H.264 seviye 5.0 verir, dikey teslim kapısından kalır); --video-bitrate BRIEF'teki platforma uygun; gerçek ` +
  `çekimli işte --video-frame-format png; Remotion'da --image-format=png --color-space=bt709), ardından 'medya ustala' ile ` +
  `ses düzeyini platform hedefine getir ` +
  `(cikti/<proje-adı>-ustalik.mp4) ve EN SON 'medya meta-temizle' (cikti/<proje-adı>-final.mp4; konum etiketi ` +
  `kalmaz, faststart). plan/kurgu.json varsa 'medya nle plan/kurgu.json --bicim hepsi' ile kurgu programı dosyalarını ` +
  `da üret (kullanıcı DaVinci Resolve / Kdenlive'da sürdürebilsin). Çıktıdan 'medya kontak' ile kare çıkarıp bak.` +
  `\nSES: ${yapimSes ? yapimSes.ozet : 'yok'}\n` +
  `GÖRSEL: ${yapimGorsel.ozet}` + isaretle('cizim'), { label: 'cizim', phase: 'Çizim', schema: YAPIM })
if (!cizim) return dur('cizim')

// ---------------------------------------------------------------- Denetim (+ düzeltme döngüsü)
const MERCEKLER = [
  { ad: 'teknik-ses', odak: 'medya denetle (plan ve müzik dosyalarıyla) ve ses ölçümleri; teknik özellikler BRIEF ile uyumlu mu' },
  { ad: 'gorsel-brief', odak: 'temas sayfaları (genel + her kesim anı): sıra, kadraj, yırtılma, boş kare, istenmeyen yazı; BRIEF uyumu (süre, en-boy, ton)' },
  { ad: 'senkron-iddia', odak: 'medya senkron (müzik varsa) ve önceki ajanların her iddiasının bir ölçümle eşlenmesi' },
]
const denetle = (tur) => parallel(MERCEKLER.map(m => () =>
  agent(`${rol('medya-denetci')}\nMERCEK: ${m.ad} — ${m.odak}. Son çıktı cikti/ altında (en yeni *-final.mp4). ` +
    `Önceki ajanların iddiaları:\nÇİZİM: ${cizim ? JSON.stringify(cizim) : 'yok'}`,
    { label: `denetci:${m.ad}:${tur}`, phase: 'Denetim', schema: BULGU })))

let denetim = await denetle(1)
if (!denetim.filter(Boolean).length) return dur('denetim')
let turlar = []
for (let tur = 1; tur <= 2; tur++) {
  const hepsi = denetim.filter(Boolean).flatMap(d => d.bulgular)
  const ciddi = hepsi.filter(b => b.ciddiyet !== 'kucuk')
  if (!ciddi.length) break
  phase('Düzeltme')
  log(`Tur ${tur}: ${ciddi.length} ciddi bulgu düzeltilecek`)
  const sorumlular = [...new Set(ciddi.map(b => b.sorumlu))]
  const duzeltmeler = await parallel(sorumlular.filter(s => s !== 'medya-hareket').map(s => () =>
    agent(`${rol(s)}\nGÖREV: bu denetim bulgularını düzelt (yalnız senin alanın):\n` +
      `${JSON.stringify(ciddi.filter(b => b.sorumlu === s))}`, { label: `duzelt:${s}:${tur}`, phase: 'Düzeltme', schema: YAPIM })))
  const yeniden = await agent(`${rol('medya-hareket')}\nGÖREV: şu bulguları düzelt (senin alanın) ve diğer ajanların ` +
    `düzeltmelerini kompozisyona yansıtıp yeniden çiz + medya ustala + EN SON medya meta-temizle (aynı dosya adları; ` +
    `plan değiştiyse medya nle ile kurgu programı dosyalarını da yenile):\n` +
    `${JSON.stringify(ciddi.filter(b => b.sorumlu === 'medya-hareket'))}\nDİĞER DÜZELTMELER: ${JSON.stringify(duzeltmeler)}`,
    { label: `yeniden-ciz:${tur}`, phase: 'Düzeltme', schema: YAPIM })
  turlar.push({ tur, bulgu: ciddi.length, duzeltmeler, yeniden })
  denetim = await denetle(tur + 1)
  if (!denetim.filter(Boolean).length) return dur('denetim', { turlar })
}

// ---------------------------------------------------------------- Rapor
phase('Rapor')
const kalan = denetim.filter(Boolean).flatMap(d => d.bulgular)
const rapor = await agent(`Proje: ${PROJE}. source ${KOK}/ortam.sh. GÖREV: cikti/RAPOR.md dosyasını TÜRKÇE yaz ` +
  `(kullanıcı için): teslim dosyalarının yolları ve boyutları; ne yapıldı (kurgu kararlarının kısa özeti); neler ` +
  `ÖLÇÜLDÜ (sayılarla: süre, çözünürlük, LUFS, gerçek tepe, senkron p90…); neler doğrulanamadı (kullanıcının ` +
  `dinlemesi/izlemesi gereken anlar, saniye saniye); kalan bulgular; açık sorular. Abartma; 'mükemmel' deme. ` +
  `Rapor metnini sonuç olarak da döndür.\nDENETİM KARARLARI: ${JSON.stringify(denetim)}\nDÜZELTME TURLARI: ` +
  `${JSON.stringify(turlar)}\nPLAN: ${JSON.stringify(plan)}`, { label: 'rapor', phase: 'Rapor' })

return {
  durum: kalan.some(b => b.ciddiyet === 'engelleyici') ? 'engelleyici_bulgu_var' : 'tamam',
  denetim: denetim.filter(Boolean).map(d => d.karar), kalan_bulgular: kalan, turlar: turlar.length, rapor,
}
