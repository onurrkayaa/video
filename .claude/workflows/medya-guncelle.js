export const meta = {
  name: 'medya-guncelle',
  description: 'Onaylanan yönetici önerilerini sırayla uygular: sabit sürümlü kurulum, kayıt, uyarlayıcı, doğruluk sınaması, beceri/belge güncellemesi; her öneriyi bağımsız doğrular, sonda tam sınama',
  whenToUse: "Kullanıcı bir medya-yonetim raporundaki önerileri onayladığında. args: {oneriler_json: 'sistem/yonetim/<tarih>-oneriler.json', onaylanan: ['O1', 'O3'], commit?: false, push?: false} — commit/push yalnız kullanıcı isterse.",
  phases: [
    { title: 'Uygula', detail: 'öneri başına (sırayla): disk denetimi, kurulum, kayıt, uyarlayıcı, sınama, belgeler' },
    { title: 'Doğrula', detail: 'öneri başına bağımsız doğrulayıcı (+ bir düzeltme turu)' },
    { title: 'Kapanış', detail: 'tam medya test, DURUM.md, (istenirse) git' },
  ],
}

// Sırayla: kurulumlar çakışmasın, fansız Mac'te ağır işler üst üste binmesin. Boş dönen ajan zinciri durdurur.
const KOK = '/Users/onurkaya/Projects/video'
if (!args || !args.oneriler_json || !args.onaylanan || !args.onaylanan.length) {
  throw new Error("args: {oneriler_json, onaylanan: ['O1', …]} gerekli")
}
const OJ = args.oneriler_json.startsWith('/') ? args.oneriler_json : `${KOK}/${args.oneriler_json}`
const ROL = `ROLÜN: önce ${KOK}/sistem/claude/agents/medya-yonetici.md dosyasını, sonra ${KOK}/sistem/claude/skills/` +
  `arac-radari/SKILL.md becerisini (benimseme adımları) oku. Her komuttan önce: source ${KOK}/ortam.sh.`

const UYG = { type: 'object', properties: {
  durum: { type: 'string', enum: ['uygulandi', 'durdu'] }, neden: { type: 'string' },
  kurulanlar: { type: 'array', items: { type: 'string' } }, degisen_dosyalar: { type: 'array', items: { type: 'string' } },
  sinamalar: { type: 'array', items: { type: 'string' } }, olcumler: { type: 'array', items: { type: 'string' } },
  disk_gb_sonra: { type: 'number' },
}, required: ['durum', 'kurulanlar', 'degisen_dosyalar', 'sinamalar', 'olcumler'] }
const DOG = { type: 'object', properties: {
  gecti: { type: 'boolean' }, bulgular: { type: 'array', items: { type: 'string' } },
}, required: ['gecti', 'bulgular'] }

const uygula = (kimlik, ek = '') => agent(`${ROL}\nGÖREV: ${OJ} içindeki ${kimlik} önerisini UYGULA (kullanıcı onayladı; ` +
  `başka öneriye dokunma). Adımlar: (1) disk: kurulum sonrası ≥ 5 GB boş + ağır ML ise ~3 GB takas payı; yetmiyorsa ` +
  `DUR (durum=durdu) ve neyin silinebileceğini yaz — kendin silme; (2) sabit sürüm/commit + SHA ile kur (Homebrew ` +
  `yok); (3) yetenekler.toml [[saglayici]] (+ gerekirse [[yetenek]]); (4) medya/komutlar uyarlayıcısı ya da güncellemesi; ` +
  `(5) testler/ altına doğruluk sınaması (ağır model ise 'agir' fikstürü); (6) ilgili beceri, CLAUDE.md, README, ` +
  `sistem/gelistirme.md, sistem/dersler.md. Ölç; ölçmediğini iddia etme. Git commit/push YAPMA.${ek}`,
  { label: `uygula:${kimlik}`, phase: 'Uygula', schema: UYG })
const dogrula = (kimlik, u) => agent(`Bağımsız, şüpheci doğrulayıcısın; ${KOK}/CLAUDE.md kurallarını bil. source ` +
  `${KOK}/ortam.sh. ${OJ} içindeki ${kimlik} önerisi uygulandı; uygulayıcının iddiaları: ${JSON.stringify(u)}. ` +
  `Doğrula: ilgili 'medya test -k …' (ağır modelse 'medya test --agir -k …'), 'medya yetenekler --saglayicilar', ` +
  `kurulan sürüm/SHA, lisans ve telemetri, belgelerin tutarlılığı (CLAUDE.md, README, beceri, yetenekler.toml), ` +
  `disk tabanı. Dosya DEĞİŞTİRME. Kanıtsız iddia = bulgu.`, { label: `dogrula:${kimlik}`, phase: 'Doğrula', schema: DOG })

const sonuc = []
for (const kimlik of args.onaylanan) {
  phase('Uygula')
  const u = await uygula(kimlik)
  if (!u) { sonuc.push({ kimlik, durum: 'yarida_kaldi' }); break }
  if (u.durum === 'durdu') { sonuc.push({ kimlik, durum: 'durdu', neden: u.neden }); continue }
  phase('Doğrula')
  let d = await dogrula(kimlik, u)
  if (d && !d.gecti) {
    log(`${kimlik}: doğrulama ${d.bulgular.length} bulgu → bir düzeltme turu`)
    const f = await uygula(kimlik, `\nDÜZELTME TURU — yalnız şu bulguları gider: ${JSON.stringify(d.bulgular)}`)
    d = f ? await dogrula(kimlik, f) : d
  }
  sonuc.push({ kimlik, durum: d && d.gecti ? 'tamam' : 'bulgu_var', uygulama: u, dogrulama: d })
}

phase('Kapanış')
const git = args.push ? 'git: değişiklikleri incele, Türkçe mesajla commit at ve git push yap (kullanıcı istedi).'
  : args.commit ? 'git: değişiklikleri incele ve Türkçe mesajla yerel commit at; push YAPMA.'
  : 'git: commit/push YAPMA; yalnız git status özetini döndür.'
const kapanis = await agent(`source ${KOK}/ortam.sh. GÖREV: (1) tam 'medya test' (hafif) çalıştır ve sonucu yaz; ` +
  `(2) ${KOK}/sistem/DURUM.md'yi güncelle: uygulanan öneriler, kalanlar, bekleyen kararlar; (3) ${git} ` +
  `Kısa Türkçe özet döndür.\nSONUÇLAR: ${JSON.stringify(sonuc)}`, { label: 'kapanis', phase: 'Kapanış' })
return { sonuc, kapanis }
