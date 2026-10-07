// Stüdyo Remotion ayarları (2026-10-05, ölçülerek seçildi — sistem/arastirma/2026-10-05/).
// Lisans anahtarı ASLA ayarlanmaz: 'free-license' dahil her anahtar remotion.pro'ya kullanım olayı gönderir.
import {Config} from '@remotion/cli/config';
import {existsSync, readdirSync} from 'node:fs';
import {homedir} from 'node:os';
import {join} from 'node:path';

// Tarayıcı: HyperFrames'in Chrome Headless Shell'i (98 MB'lık ikinci indirmeyi önler). Bulunamazsa Remotion kendi
// sınanmış sürümünü indirir (storage.googleapis.com) — bu durumda uyarı yazılır.
const kok = join(homedir(), '.cache/hyperframes/chrome/chrome-headless-shell');
const surum = existsSync(kok) ? readdirSync(kok).filter((d) => d.startsWith('mac_arm-')).sort().at(-1) : undefined;
const chrome = surum ? join(kok, surum, 'chrome-headless-shell-mac-arm64', 'chrome-headless-shell') : undefined;
if (chrome && existsSync(chrome)) {
	Config.setBrowserExecutable(chrome);
} else {
	console.warn('⚠ HyperFrames Chrome bulunamadı; Remotion kendi Chrome Headless Shell sürümünü indirecek (~98 MB).');
}

Config.setRspack(true); // hızlı paketleme
Config.setChromiumOpenGlRenderer('angle'); // WebGL/3B sahnelerde ~3,6x hızlı (ölçüldü)
Config.setColorSpace('bt709'); // etiketli bt709 tv çıktı; etiketsiz bt601 renk kayması yapar
Config.setConcurrency(4); // fansız M2: 4 sekme
// Son çizimde: --image-format=png --color-space=bt709 (bağımsız ölçüm VMAF 96,97 → 98,80, en kötü kare 93 → 95;
// süre ×1,24). bt709 ŞART: varsayılan etiketsiz BT.601 HD oynatıcıda renk kaydırır. Taslakta JPEG yeter.
