// Yazısız 3B örnek (@remotion/three + React Three Fiber): ışıklı, kareyle dönen bir düğüm; yay (spring) girişi.
// Kurallar: ThreeCanvas'a width/height ver; her hareket useCurrentFrame()'den gelir (R3F useFrame YASAK: çizimde
// titrer); ThreeCanvas içindeki <Sequence> layout="none". Model/doku gerekiyorsa public/ altında yerel dosya (uzak yok).
// Çizim remotion.config.ts'deki gl = 'angle' ile GPU'da (ANGLE Metal); ölçüm: sistem/devam/remotion-3b/2026-10-09/.
import {ThreeCanvas} from '@remotion/three';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export const Ornek3B: React.FC = () => {
	const kare = useCurrentFrame();
	const {fps, width, height, durationInFrames} = useVideoConfig();
	const giris = spring({frame: kare, fps, config: {damping: 200}}); // aşmasız, yumuşak oturma
	const donus = interpolate(kare, [0, durationInFrames], [0, Math.PI * 2]); // süre boyunca tam tur
	return (
		<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 40%, #1d3b5c, #0b1d33)'}}>
			{/* Tuval saydam: arka plan CSS'ten gelir. */}
			<ThreeCanvas width={width} height={height} camera={{fov: 40, position: [0, 0, 9]}}>
				<ambientLight intensity={0.35} />
				<directionalLight position={[4, 6, 5]} intensity={2.2} />
				<pointLight position={[-5, -3, 2]} intensity={30} color="#3fa7d6" />
				<mesh rotation={[donus * 0.5, donus, 0]} scale={giris * 0.8}>
					<torusKnotGeometry args={[1, 0.32, 256, 32]} />
					<meshStandardMaterial color="#f26b5b" roughness={0.35} metalness={0.25} />
				</mesh>
			</ThreeCanvas>
		</AbsoluteFill>
	);
};
