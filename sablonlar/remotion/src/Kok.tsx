import {Composition} from 'remotion';
import {Ornek} from './Ornek';
import {Ornek3B} from './Ornek3B';
import {OrnekLottie} from './OrnekLottie';

// Bir projede birden çok kompozisyon olabilir (ör. 9:16 ve 16:9 sürüm). Süreler KARE cinsindendir.
// Ornek3B ve OrnekLottie başvurudur: kullanılmıyorsa satırını ve dosyasını sil (three/lottie-web pakete girmesin).
export const Kok: React.FC = () => {
	return (
		<>
			<Composition id="Ornek" component={Ornek} durationInFrames={120} fps={30} width={1080} height={1920} />
			<Composition id="Ornek3B" component={Ornek3B} durationInFrames={90} fps={30} width={1080} height={1920} />
			{/* Süre = Lottie JSON'un op'u (60 kare); daha uzun gerekiyorsa <Lottie loop />. */}
			<Composition id="OrnekLottie" component={OrnekLottie} durationInFrames={60} fps={30} width={1080} height={1920} />
		</>
	);
};
