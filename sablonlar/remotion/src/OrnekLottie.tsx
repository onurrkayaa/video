// Yazısız Lottie örneği (@remotion/lottie + lottie-web): public/lottie/ornek.json — stüdyoda kodla yazıldı (üçüncü
// taraf içerik yok). Kurallar: Lottie dosyası YEREL (public/ + staticFile; lottiefiles.com gibi uzak adres yok),
// kullanıcının dosyası public/ altına kopyalanır (symlink değil). 1 Remotion karesi = 1 Lottie karesi: JSON'daki `fr`
// kompozisyonun fps'inden farklıysa hız değişir → aynı fps'te kur ya da playbackRate={fr / fps} ver.
import {Lottie, LottieAnimationData} from '@remotion/lottie';
import {useEffect, useState} from 'react';
import {AbsoluteFill, cancelRender, continueRender, delayRender, staticFile} from 'remotion';

export const OrnekLottie: React.FC = () => {
	const [bekle] = useState(() => delayRender('Lottie JSON yükleniyor'));
	const [veri, setVeri] = useState<LottieAnimationData | null>(null);

	useEffect(() => {
		fetch(staticFile('lottie/ornek.json'))
			.then((yanit) => yanit.json())
			.then((json) => {
				setVeri(json);
				continueRender(bekle);
			})
			.catch((hata) => cancelRender(hata));
	}, [bekle]);

	return (
		<AbsoluteFill style={{background: '#0e2a1f', justifyContent: 'center', alignItems: 'center'}}>
			{veri ? <Lottie animationData={veri} style={{width: 900, height: 900}} /> : null}
		</AbsoluteFill>
	);
};
