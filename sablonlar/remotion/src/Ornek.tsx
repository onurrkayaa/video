// Yazısız örnek: yay (spring) girişi, kare ızgarasında zamanlama, motivasyonlu geçiş (TransitionSeries).
// Yazı yalnız kullanıcı isterse eklenir; o zaman yerel woff2 için ./fontlar.ts kullanılır (lang tr dikkat).
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {linearTiming, springTiming, TransitionSeries} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';

const Sahne: React.FC<{renk: string; vurgu: string}> = ({renk, vurgu}) => {
	const kare = useCurrentFrame();
	const {fps} = useVideoConfig();
	const giris = spring({frame: kare, fps, config: {damping: 200}}); // aşmasız, yumuşak oturma
	const nefes = interpolate(kare, [0, 60], [1, 1.06], {extrapolateRight: 'clamp'}); // yavaş itme (push-in)
	return (
		<AbsoluteFill style={{background: `radial-gradient(circle at 50% 40%, ${vurgu}, ${renk})`}}>
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', transform: `scale(${nefes})`}}>
				<div
					style={{
						width: 420,
						height: 420,
						borderRadius: '50%',
						border: `24px solid ${vurgu}`,
						transform: `scale(${giris}) rotate(${(1 - giris) * -90}deg)`,
						opacity: giris,
					}}
				/>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

export const Ornek: React.FC = () => {
	return (
		<TransitionSeries>
			<TransitionSeries.Sequence durationInFrames={60}>
				<Sahne renk="#0b1d33" vurgu="#3fa7d6" />
			</TransitionSeries.Sequence>
			<TransitionSeries.Transition presentation={slide({direction: 'from-right'})} timing={springTiming({config: {damping: 200}, durationInFrames: 15})} />
			<TransitionSeries.Sequence durationInFrames={50}>
				<Sahne renk="#2b0f1e" vurgu="#f26b5b" />
			</TransitionSeries.Sequence>
			<TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 10})} />
			<TransitionSeries.Sequence durationInFrames={35}>
				<Sahne renk="#0e2a1f" vurgu="#6cc58d" />
			</TransitionSeries.Sequence>
		</TransitionSeries>
	);
};
