export const meta = {
  name: 'medya-denetim',
  description: 'Bir medya çıktısının bağımsız, çok mercekli ve şüpheci denetimi: teknik/ses ölçümü, görsel/brief uyumu, senkron ve iddia doğrulaması; birleşik karar',
  whenToUse: "Bir video/ses/görsel teslim edilmeden önce. args: {cikti: 'yol', proje?: 'projeler/…', hedef?: 'web|sosyal|youtube|arsiv', brief?: 'beklenenler'}",
  phases: [
    { title: 'Mercekler', detail: 'üç bağımsız denetçi paralel' },
    { title: 'Karar', detail: 'bulguları birleştir, çelişkileri ölçümle çöz, karar ver' },
  ],
}

const KOK = '/Users/onurkaya/Projects/video'
if (!args || !args.cikti) throw new Error("args.cikti gerekli, ör. {cikti: 'projeler/x/cikti/x-final.mp4'}")
const CIKTI = args.cikti.startsWith('/') ? args.cikti : `${KOK}/${args.cikti}`
const PROJE = args.proje ? (args.proje.startsWith('/') ? args.proje : `${KOK}/${args.proje}`) : null
const BAGLAM = `Denetlenecek çıktı: ${CIKTI}. ${PROJE ? `Proje: ${PROJE} (BRIEF.md, KARARLAR.md, plan/kurgu.json, analiz/muzik.json varsa kullan).` : ''} ` +
  `${args.hedef ? `Hedef platform: ${args.hedef}.` : ''} ${args.brief ? `Beklenenler: ${args.brief}.` : ''} ` +
  `Her komuttan önce: source ${KOK}/ortam.sh. ROLÜN: önce ${KOK}/sistem/claude/agents/medya-denetci.md dosyasını oku; ` +
  `talimatları önceliklidir. Hiçbir dosyayı değiştirme.`

const BULGU = { type: 'object', properties: {
  karar: { type: 'string', enum: ['GECTI', 'KALDI'] },
  bulgular: { type: 'array', items: { type: 'object', properties: {
    ciddiyet: { type: 'string', enum: ['engelleyici', 'onemli', 'kucuk'] }, ne: { type: 'string' },
    nerede: { type: 'string' }, kanit: { type: 'string' }, oneri: { type: 'string' } },
    required: ['ciddiyet', 'ne', 'kanit', 'oneri'] } },
  olculemeyenler: { type: 'array', items: { type: 'string' } },
}, required: ['karar', 'bulgular', 'olculemeyenler'] }

const MERCEKLER = [
  ['teknik-ses', 'medya denetle (varsa --plan ve --muzik ile) + ses ölçümleri (LUFS, gerçek tepe, kırpılma, kesimde tık) + teknik özellikler'],
  ['gorsel-brief', 'temas sayfaları: genel (--aralik 1) ve her kesim anı (--anlar); sıra, kadraj, yırtılma, boş/siyah kare, istenmeyen yazı; BRIEF uyumu'],
  ['senkron-iddia', 'müzik varsa medya senkron; plan ve KARARLAR.md içindeki her iddianın ölçümle eşlenmesi; ölçülemeyenlerin listesi'],
]

phase('Mercekler')
const sonuclar = await parallel(MERCEKLER.map(([ad, odak]) => () =>
  agent(`${BAGLAM}\nMERCEK: ${ad} — ${odak}. Sorun bulmaya çalış; kanıtsız GEÇTİ verme.`,
    { label: `mercek:${ad}`, phase: 'Mercekler', schema: BULGU })))

phase('Karar')
const karar = await agent(`${BAGLAM}\nÜç bağımsız denetçinin bulguları aşağıda. Aynı bulguları birleştir; çelişen ` +
  `bulguyu ilgili ölçümü yeniden çalıştırarak çöz; tek bir karar ver. Engelleyici bulgu varsa KALDI.\n` +
  `${JSON.stringify(sonuclar)}`, { label: 'karar', phase: 'Karar', schema: BULGU })

return { karar, mercekler: sonuclar }
