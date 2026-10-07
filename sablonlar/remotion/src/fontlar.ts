// Yerel yazı tipleri (Google Fonts YOK). Türkçe için latin + latin-ext dosyaları birlikte yüklenir.
// Kullanım: kompozisyon dosyasının en üstünde `import './fontlar';` ve style={{fontFamily: 'Inter'}}.
// public/fonts/ içine dosyaları KOPYALA ya da hard-link yap (symlink Remotion sunucusunda 404 verir — ölçüldü).
import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

const agirliklar = ['400', '600', '700'];
for (const w of agirliklar) {
	for (const alt of ['latin', 'latin-ext']) {
		loadFont({family: 'Inter', url: staticFile(`fonts/inter-${alt}-${w}-normal.woff2`), weight: w});
	}
}
