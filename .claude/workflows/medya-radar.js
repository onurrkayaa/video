export const meta = {
  name: 'medya-radar',
  description: 'Teknoloji radarı: her medya alanında bilgi tabanından sonra çıkan yerel ve ücretsiz araç/modelleri tarar, şüpheci doğrular, stüdyo için öneri raporu yazar (kurulum yapmaz)',
  whenToUse: "Ayda bir ya da yeni bir araç duyulduğunda. args: {alanlar?: ['video-framework', …], konu?: 'belirli araç/model adı'}",
  phases: [
    { title: 'Tara', detail: 'alan başına gözcü: yeni sürümler, yeni modeller, lisans değişiklikleri' },
    { title: 'Doğrula', detail: 'öneri başına şüpheci: lisans, Apple Silicon, boyut, gerçekten daha iyi mi' },
    { title: 'Rapor', detail: 'sistem/radar/<tarih>-radar.md + önerilen yetenekler.toml girdileri' },
  ],
}

const KOK = '/Users/onurkaya/Projects/video'
const TUM = ['video-framework', 'editing-craft', 'footage-analysis', 'music-sync', 'audio-production',
  'image-photo', 'animation-motion', 'claude-code-ecosystem', 'delivery-qa']
const ALANLAR = (args && args.alanlar && args.alanlar.length) ? args.alanlar : TUM
const KONU = args && args.konu ? `\nÖZEL KONU (öncelikli): ${args.konu}` : ''
const ROL = `ROLÜN: önce ${KOK}/sistem/claude/agents/medya-gozcu.md dosyasını oku; talimatları önceliklidir. ` +
  `Hiçbir şey kurma; ayar değiştirme. source ${KOK}/ortam.sh.`

const ONERI = { type: 'object', properties: {
  alan: { type: 'string' },
  oneriler: { type: 'array', items: { type: 'object', properties: {
    arac: { type: 'string' }, ne_icin: { type: 'string' }, mevcut_saglayici: { type: 'string' },
    neden_daha_iyi: { type: 'string' }, lisans_kod: { type: 'string' }, lisans_agirlik: { type: 'string' },
    ticari: { type: 'string' }, apple_silicon: { type: 'string' }, boyut_mb: { type: 'number' },
    kurulum: { type: 'string' }, kanit_tarihli: { type: 'array', items: { type: 'string' } },
    karar: { type: 'string', enum: ['benimse', 'izle', 'reddet'] } },
    required: ['arac', 'ne_icin', 'neden_daha_iyi', 'lisans_kod', 'ticari', 'kanit_tarihli', 'karar'] } },
  degisiklik_yok: { type: 'boolean' },
}, required: ['alan', 'oneriler', 'degisiklik_yok'] }
const DOGRU = { type: 'object', properties: {
  arac: { type: 'string' }, gecerli: { type: 'boolean' }, duzeltmeler: { type: 'string' },
  sinama_onerisi: { type: 'string', description: 'testler/ altına eklenecek doğruluk sınaması' },
}, required: ['arac', 'gecerli', 'duzeltmeler'] }

const sonuc = await pipeline(
  ALANLAR,
  (alan) => agent(`${ROL}\nALAN: ${alan}. Bilgi tabanı: en yeni ${KOK}/sistem/arastirma/<tarih>/${alan}.md ve ` +
    `${KOK}/yetenekler.toml. O tarihten bu yana çıkan/gelişen yerel ve ücretsiz araç, model, sürüm ve lisans ` +
    `değişikliklerini web'de araştır (birincil kaynaklar). Yalnız ÖLÇÜLEBİLİR biçimde daha iyi olanları 'benimse' ` +
    `öner; emin değilsen 'izle'.${KONU}`, { label: `tara:${alan}`, phase: 'Tara', schema: ONERI }),
  (o) => parallel((o ? o.oneriler.filter(x => x.karar !== 'reddet') : []).map(x => () =>
    agent(`${ROL}\nŞÜPHECİ DOĞRULAMA: şu öneriyi çürütmeye çalış (lisans kod+ağırlık, ticari kullanım, M2 16 GB ` +
      `uyumu, disk, bakım, gerçekten mevcut sağlayıcıdan iyi mi). Emin değilsen gecerli=false.\n${JSON.stringify(x)}`,
      { label: `dogrula:${x.arac}`, phase: 'Doğrula', schema: DOGRU }).then(d => ({ ...x, dogrulama: d })))),
)

phase('Rapor')
const tumu = sonuc.filter(Boolean).flat()
const rapor = await agent(`${ROL}\nGÖREV: ${KOK}/sistem/radar/ altına '<bugünün tarihi (date +%F)>-radar.md' adlı ` +
  `TÜRKÇE bir rapor yaz: doğrulanmış 'benimse' önerileri (her biri için önerilen [[saglayici]] TOML girdisi, ` +
  `uyarlayıcı ve sınama taslağı), 'izle' listesi, reddedilenler ve nedenleri, değişiklik olmayan alanlar. ` +
  `Kullanıcı onayı olmadan hiçbir şeyin kurulmayacağını belirt. Rapor yolunu ve 5 maddelik özeti döndür.\n` +
  `${JSON.stringify(tumu)}`, { label: 'rapor', phase: 'Rapor' })

return { oneriler: tumu.filter(x => x.dogrulama && x.dogrulama.gecerli), rapor }
