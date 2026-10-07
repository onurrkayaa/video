import {Composition} from 'remotion';
import {Ornek} from './Ornek';

// Bir projede birden çok kompozisyon olabilir (ör. 9:16 ve 16:9 sürüm). Süreler KARE cinsindendir.
export const Kok: React.FC = () => {
	return (
		<Composition id="Ornek" component={Ornek} durationInFrames={120} fps={30} width={1080} height={1920} />
	);
};
