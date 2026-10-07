export const meta = {
  name: 'medya-beceri-yaz',
  description: 'Stüdyo becerilerini yaz (ya da diskteki yazılmışı al), beceriyle senaryoya uygulayıp şüpheci incele, gerekirse düzelt',
  whenToUse: "sistem/claude/skills altındaki stüdyo becerilerini yazmak/güncellemek. Tanımlar diskte: sistem/devam/beceri-tanimlari.json ({ortak:{baglam,bicim}, beceriler:{ad:{kapsam, disinda, kaynaklar[], senaryo, degisken, ek?, onceki?, yama?}}}). args: {beceriler:[{ad, yazildi?, taban_hatalari?}], tanim_dosyasi?, taban_klasoru?}. yazildi:true → yazıcı atlanır (dosyalar diskte; yarıda kalan koşudan devam).",
  phases: [
    { title: 'Yaz', detail: 'araştırma + taban (RED) hatalarından beceri ya da yama' },
    { title: 'İncele', detail: 'beceriyle iki senaryoyu planla + şüpheci doğruluk/uyum/biçim denetimi' },
    { title: 'Düzelt', detail: 'bulguları uygula' },
  ],
}

// Kullanım sınırına dayanıklılık: her beceri kendi zincirinde; biri boş dönerse yalnız o beceri 'hata' olur.
// Devam ederken önbellek SIRAYA bağlıdır (değişen/bitmemiş ilk çağrıdan sonrası yeniden koşar) → yarıda kalan
// beceriyi yazildi:true ile yeni bir koşuda sürdür.
const KOK = '/Users/onurkaya/Projects/video'
const TANIM = args.tanim_dosyasi || `${KOK}/sistem/devam/beceri-tanimlari.json`
const SKILLS = args.beceriler
const TABAN = args.taban_klasoru || `${KOK}/sistem/devam/ham`
// Uzun tanım metinleri istemlere gömülmez: ajan kendi girdisini dosyadan okur (args kısa kalır, devam kolay olur).
const ORTAK = {
  baglam: `STUDIO CONTEXT, USER RULES and FEEDBACK: read the "ortak.baglam" field of ${TANIM} first — it is binding.`,
  bicim: `SKILL FORMAT: read the "ortak.bicim" field of ${TANIM} — it is binding.`,
}
const TANIMI = (s) => `YOUR SKILL SPEC: the entry beceriler["${s.ad}"] in ${TANIM} — fields kapsam (SCOPE), disinda (NOT IN SCOPE: ` +
  `cross-reference those sibling skills by name), kaynaklar (research files in ${KOK}/sistem/arastirma/2026-10-05/; ` +
  `"Şüpheci doğrulama/Düzeltmeler" sections OVERRIDE the picks; newer files override older ones), senaryo, degisken, ` +
  `ek (FACTS MEASURED IN THIS STUDIO — authoritative, newer than the research), onceki (drafts), yama (patch mode).`

const WRITE = { type: 'object', properties: {
  dosyalar: { type: 'array', items: { type: 'string' } },
  silinenler: { type: 'array', items: { type: 'string' } },
  taban_hatalari: { type: 'array', items: { type: 'string' }, description: 'baseline failures the skill now prevents (and where)' },
  saglayici_onerileri: { type: 'array', items: { type: 'object', properties: {
    ad: { type: 'string' }, amac: { type: 'string' }, lisans: { type: 'string' }, ticari: { type: 'string' },
    kurulum: { type: 'string' }, kontrol: { type: 'string' }, boyut_mb: { type: 'number' }, kanit: { type: 'string' } },
    required: ['ad', 'amac', 'lisans', 'ticari', 'kurulum', 'kontrol', 'boyut_mb'] } },
  medya_onerileri: { type: 'array', items: { type: 'string' }, description: 'logic that belongs in the medya CLI rather than a skill script' },
  kelime_sayisi: { type: 'number' },
  notlar: { type: 'string' },
}, required: ['dosyalar', 'taban_hatalari', 'saglayici_onerileri', 'kelime_sayisi'] }

const REVIEW = { type: 'object', properties: {
  plan_ozeti: { type: 'string', description: 'short with-skill plans for both scenarios (evidence for compliance)' },
  dogruluk_sorunlari: { type: 'array', items: { type: 'object', properties: {
    dosya: { type: 'string' }, iddia: { type: 'string' }, sorun: { type: 'string' }, duzeltme: { type: 'string' }, kanit: { type: 'string' } },
    required: ['dosya', 'iddia', 'sorun', 'duzeltme'] } },
  uyum_sorunlari: { type: 'array', items: { type: 'string' } },
  bicim_sorunlari: { type: 'array', items: { type: 'string' } },
  betik_sorunlari: { type: 'array', items: { type: 'string' } },
  karar: { type: 'string', enum: ['gecti', 'duzeltilmeli'] },
}, required: ['plan_ozeti', 'dogruluk_sorunlari', 'uyum_sorunlari', 'bicim_sorunlari', 'betik_sorunlari', 'karar'] }

const TASARRUF = 'Be economical: grep/read only the sections you need, do not re-read files, run only cheap commands (--help, tiny fixtures in the scratchpad), never long renders or installs.'

const yazPrompt = (s) => `You are writing a Claude Code Agent Skill for a local media studio. ${ORTAK.baglam}

${ORTAK.bicim}

SKILL: name "${s.ad}" → directory ${KOK}/sistem/claude/skills/${s.ad}/ (write ONLY inside it).
${TANIMI(s)}
ALSO READ: ${KOK}/CLAUDE.md, ${KOK}/sistem/dersler.md (lessons — authoritative).
If the spec has "yama": PATCH the existing, already reviewed skill — change only what it requires.
If the spec has "onceki": those are DRAFTS from interrupted earlier attempts in the skill directory; nobody reviewed them. Keep a draft only if the skill needs it, it does not duplicate a medya command, and you ran it successfully on a tiny fixture; otherwise fix or delete it (agent outputs, not user files).
BASELINE (RED): an agent WITHOUT this skill answered the spec's senaryo. Its plan: ${TABAN}/taban-${s.ad}.json (fields plan, varsayimlar, dogrulama) — read it.
Write the skill so the baseline's specific failures (wrong tools, unmeasured claims, license problems, amateur craft, missing verification, wrong flags, unrequested scope) cannot recur, plus what the scope needs — nothing speculative. Verify every command/flag you write locally where cheap (source ${KOK}/ortam.sh; 'medya <cmd> --help'; 'arac/ffmpeg -h filter=<name>'; 'node_modules/.bin/hyperframes <cmd> --help'). Never reference a medya subcommand, flag or file that does not exist; tools not installed get an exact install command in a reference file and go to saglayici_onerileri (do NOT install). ${TASARRUF}`

const incelePrompt = (s, w) => `You are an adversarial reviewer of a Claude Code skill for a local media studio. ${ORTAK.baglam}

${ORTAK.bicim}

Skill under review: ${KOK}/sistem/claude/skills/${s.ad}/ (read every file).
${TANIMI(s)} The skill must agree with those research files, the "ek" facts, ${KOK}/CLAUDE.md and ${KOK}/sistem/dersler.md.
Baseline (agent without the skill): ${TABAN}/taban-${s.ad}.json. Failures the writer claims to have fixed: ${JSON.stringify(w.taban_hatalari)}

STEP 1 — apply: act as an agent that loaded this skill because it matched, and write a short concrete plan (tools, exact commands, order, verification, what you tell the user) for the spec's "senaryo" (scenario 1) and "degisken" (scenario 2).
STEP 2 — try to REFUTE the skill:
1. Accuracy: every command, flag, filter option, parameter value, license and size claim — check locally (source ${KOK}/ortam.sh; medya <cmd> --help; arac/ffmpeg -h filter=X; hyperframes --help) and against the research. A medya subcommand/flag that does not exist is an error.
2. Scripts: run each file in scripts/ with --help and once on a tiny fixture (scratchpad outputs only); report crashes, wrong results, duplication of medya commands.
3. Compliance: would your STEP 1 plans (following the skill) repeat the baseline failures or break studio rules (on-screen text without asking, unmeasured claims, cloud/paid tools, NC-licensed tools for work, skipped verification, music-sync claims without medya senkron, opening intimate frames without asking)? Where the skill was missing/ambiguous for the scenarios, that is a finding.
4. Format: description starts with "Use when", <= 500 chars, triggers only, English with Turkish keywords; SKILL.md body <= 650 words; references exist and are linked by relative path; no narrative.
Default to 'duzeltilmeli' if any real problem exists. Give precise, actionable fixes. ${TASARRUF}`

const duzeltPrompt = (s, r) => `Apply these review findings to the skill at ${KOK}/sistem/claude/skills/${s.ad}/ (edit only inside that directory). ${ORTAK.baglam}
${ORTAK.bicim}
Findings: ${JSON.stringify(r)}
Verify every changed command/flag locally (source ${KOK}/ortam.sh) and re-run any script you change on a tiny fixture. Keep SKILL.md body <= 650 words. Return the same structure as the writer. ${TASARRUF}`

const sonuclar = await pipeline(
  SKILLS,
  (s) => s.yazildi
    ? { w: { taban_hatalari: s.taban_hatalari || ['(yazıcı önceki koşuda bitti; taban dosyasını kendin oku)'], dosyalar: [], saglayici_onerileri: [] } }
    : agent(yazPrompt(s), { label: `yaz:${s.ad}`, phase: 'Yaz', schema: WRITE, effort: 'high' })
        .then(w => { if (!w) throw new Error('yazıcı boş döndü'); return { w } }),
  (x, s) => agent(incelePrompt(s, x.w), { label: `incele:${s.ad}`, phase: 'İncele', schema: REVIEW, effort: 'high' })
    .then(r => { if (!r) throw new Error('inceleyici boş döndü'); return { ...x, r } }),
  (x, s) => x.r.karar === 'duzeltilmeli'
    ? agent(duzeltPrompt(s, x.r), { label: `düzelt:${s.ad}`, phase: 'Düzelt', schema: WRITE, effort: 'medium' }).then(f => ({ ...x, f }))
    : x,
)

return sonuclar.map((x, i) => x ? ({
  ad: SKILLS[i].ad,
  taban_hatalari: x.w && x.w.taban_hatalari,
  dosyalar: (x.f && x.f.dosyalar) || (x.w && x.w.dosyalar),
  silinenler: [...((x.w && x.w.silinenler) || []), ...((x.f && x.f.silinenler) || [])],
  kelime: (x.f && x.f.kelime_sayisi) || (x.w && x.w.kelime_sayisi),
  saglayici_onerileri: [...((x.w && x.w.saglayici_onerileri) || []), ...((x.f && x.f.saglayici_onerileri) || [])],
  medya_onerileri: [...((x.w && x.w.medya_onerileri) || []), ...((x.f && x.f.medya_onerileri) || [])],
  inceleme: x.r,
  duzeltildi: !!x.f,
  duzeltme_bos: x.r && x.r.karar === 'duzeltilmeli' && !x.f,
}) : { ad: SKILLS[i].ad, hata: 'zincir yarıda kaldı (journal.jsonl); yazildi:true ile sürdür' })
