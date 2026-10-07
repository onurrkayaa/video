export const meta = {
  name: 'medya-yonetim',
  description: 'Stüdyo yöneticisi (baş ajan): durum incelemesi ve isteğe bağlı teknoloji radarı; öncelikli, maliyetli, şüpheci doğrulanmış öneriler hazırlar (kurulum yapmaz)',
  whenToUse: "Kullanıcı öneri, durum, 'ne yapalım', 'yeni çıkanları araştır / sistemi güncelle' dediğinde ya da son yönetici incelemesinden 30 gün geçtiğinde (oturum özeti söyler). args: {radar?: boolean (yeni araç/model taraması, ağır), alanlar?: string[], konu?: string}. Onaylanan öneriler medya-guncelle ile uygulanır.",
  phases: [
    { title: 'Envanter', detail: 'sağlık, sürümler, bekleyen kararlar, birikim, proje bulguları' },
    { title: 'Radar', detail: 'isteğe bağlı: medya-radar (alan başına gözcü + şüpheci)' },
    { title: 'Öneri', detail: 'yönetici: en çok 7 öncelikli öneri' },
    { title: 'Doğrula', detail: 'öneri başına şüpheci: sürüm, lisans, boyut, iddia' },
    { title: 'Rapor', detail: 'sistem/yonetim/<tarih>-oneriler.md + .json' },
  ],
}

// Kullanım sınırına dayanıklılık: aşama boş dönerse yarım çıktıyla sürmez; aynı oturumda resumeFromRunId.
const KOK = '/Users/onurkaya/Projects/video'
const A = args || {}
const ROL = `ROLÜN: önce ${KOK}/sistem/claude/agents/medya-yonetici.md dosyasını oku; talimatları önceliklidir. ` +
  `Hiçbir şey kurma, silme, ayar değiştirme. Her komuttan önce: source ${KOK}/ortam.sh.`
const dur = (asama) => ({ durum: 'yarida_kaldi', asama, devam: 'Aynı oturumda Workflow({scriptPath, resumeFromRunId}).' })

const ENV = { type: 'object', properties: {
  ozet: { type: 'string' },
  saglik: { type: 'object', properties: {
    test: { type: 'string' }, eksik_saglayicilar: { type: 'array', items: { type: 'string' } },
    disk_gb: { type: 'number' }, takas: { type: 'string' }, git: { type: 'string' } },
    required: ['test', 'disk_gb', 'git'] },
  surumler: { type: 'array', items: { type: 'object', properties: {
    bilesen: { type: 'string' }, kurulu: { type: 'string' }, guncel: { type: 'string' }, kaynak: { type: 'string' },
    not: { type: 'string', description: 'kırıcı değişiklik, lisans/telemetri değişikliği, öneme dair' } },
    required: ['bilesen', 'kurulu', 'guncel', 'kaynak'] } },
  bekleyen_kararlar: { type: 'array', items: { type: 'string' } },
  birikim: { type: 'array', items: { type: 'string' }, description: 'gelistirme.md ve proje raporlarından öne çıkanlar' },
}, required: ['ozet', 'saglik', 'surumler', 'bekleyen_kararlar', 'birikim'] }

const ONERI = { type: 'object', properties: {
  oneriler: { type: 'array', items: { type: 'object', properties: {
    kimlik: { type: 'string' }, kategori: { type: 'string', enum: ['duzeltme', 'guncelleme', 'yeni-yetenek', 'bakim'] },
    ne: { type: 'string' }, neden: { type: 'string' }, deger: { type: 'string' },
    maliyet: { type: 'object', properties: { disk_mb: { type: 'number' }, sure: { type: 'string' }, risk: { type: 'string' } },
      required: ['disk_mb', 'sure', 'risk'] },
    lisans: { type: 'string' }, ticari: { type: 'string' },
    kullanici_karari: { type: 'boolean' }, karar_nedeni: { type: 'string' },
    dogrulama_plani: { type: 'string' }, kaynaklar: { type: 'array', items: { type: 'string' } } },
    required: ['kimlik', 'kategori', 'ne', 'neden', 'deger', 'maliyet', 'lisans', 'ticari', 'kullanici_karari',
      'dogrulama_plani', 'kaynaklar'] } },
}, required: ['oneriler'] }

const DOGRU = { type: 'object', properties: {
  gecerli: { type: 'boolean' }, duzeltmeler: { type: 'string' },
  dogrulanan: { type: 'array', items: { type: 'string' } }, dogrulanamayan: { type: 'array', items: { type: 'string' } },
}, required: ['gecerli', 'duzeltmeler', 'dogrulanan', 'dogrulanamayan'] }

const RAPOR = { type: 'object', properties: {
  md: { type: 'string', description: 'yazılan .md dosyasının yolu' }, json: { type: 'string' },
  ozet: { type: 'string', description: '3 satır Türkçe özet' },
  tablo: { type: 'string', description: 'markdown öneri tablosu: kimlik | ne | değer | maliyet | karar gerekir mi' },
}, required: ['md', 'json', 'ozet', 'tablo'] }

phase('Envanter')
const envanter = await agent(`${ROL}\nGÖREV: stüdyonun envanterini çıkar (rolündeki "Bakacağın yerler" 1–3). ` +
  `Sürümleri birincil kaynaktan al (npm, PyPI, GitHub releases, Hugging Face API). Dosya yazma; JSON döndür.`,
  { label: 'envanter', phase: 'Envanter', schema: ENV })
if (!envanter) return dur('envanter')

let radar = null
if (A.radar) {
  phase('Radar')
  try {
    radar = await workflow({ scriptPath: `${KOK}/.claude/workflows/medya-radar.js` },
      { alanlar: A.alanlar, konu: A.konu })
  } catch (e) {
    log(`radar çalışmadı (${e}); öneriler yalnız envantere dayanacak`)
  }
}

phase('Öneri')
const oneri = await agent(`${ROL}\nGÖREV: aşağıdaki envanter${radar ? ' ve radar sonuçlarından' : 'den'} en çok 7 ` +
  `öncelikli öneri çıkar (rolündeki "Öneri biçimi"). Dosya yazma; JSON döndür.${A.konu ? `\nKULLANICININ KONUSU: ${A.konu}` : ''}` +
  `\nENVANTER: ${JSON.stringify(envanter)}${radar ? `\nRADAR: ${JSON.stringify(radar)}` : ''}`,
  { label: 'oneri', phase: 'Öneri', schema: ONERI })
if (!oneri) return dur('oneri')

phase('Doğrula')
const dogrulanmis = (await parallel(oneri.oneriler.map(o => () =>
  agent(`${ROL}\nŞÜPHECİ DOĞRULAMA: bu öneriyi çürütmeye çalış — sürüm ve tarih (birincil kaynak), lisans (kod + ` +
    `ağırlık; ticari kullanım), boyut ve disk tabanı (5 GB + ağır ML'de takas payı), M2 16 GB uyumu, mevcut ` +
    `sağlayıcıdan gerçekten iyi mi, doğrulama planı yeterli mi. Emin değilsen gecerli=false.\n${JSON.stringify(o)}`,
  { label: `dogrula:${o.kimlik}`, phase: 'Doğrula', schema: DOGRU }).then(d => ({ ...o, dogrulama: d })))))
  .filter(Boolean)

phase('Rapor')
const rapor = await agent(`${ROL}\nGÖREV: ${KOK}/sistem/yonetim/ altına '<date +%F>-oneriler.md' (Türkçe, kullanıcı ` +
  `için: 3 satır özet; sağlık; sürüm farkları; öneriler — her biri için doğrulama sonucu, düzeltmeler ve ` +
  `"kullanıcı kararı gerekir mi"; bekleyen kararlar) ve aynı adla '.json' (öneriler dizisi, doğrulama dahil) yaz. ` +
  `Şüphecinin geçersiz saydığı öneriyi "doğrulanamadı" bölümüne taşı. Yolları, özeti ve tabloyu döndür.\n` +
  `ENVANTER: ${JSON.stringify(envanter)}\nÖNERİLER: ${JSON.stringify(dogrulanmis)}`,
  { label: 'rapor', phase: 'Rapor', schema: RAPOR })
if (!rapor) return dur('rapor')

return { rapor, oneriler: dogrulanmis.map(o => ({ kimlik: o.kimlik, ne: o.ne, gecerli: o.dogrulama && o.dogrulama.gecerli,
  kullanici_karari: o.kullanici_karari })) }
