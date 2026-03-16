import React, {useRef, useState, useEffect} from 'react';
import {useSetAtom, useAtom} from 'jotai';
import {bonusPerRound, getCurrentRound} from '@/shared/api/betting.ts';
import Lottie, {type LottieRefCurrentProps} from 'lottie-react';
import {BubbleLoading, createBubbleSpec} from '@/features/bubble-game';
import {userAtom} from '@/atom/userAtom.ts';
import {gameAtom} from '@/atom/gameAtom.ts';
import {useTelegramWebApp} from '@/shared/lib';

type PopSpec = {
    size: number;
    top: number;
    left: number;
    data: any;
    id: number;
    showScore?: boolean;
};

export const BubbleGame: React.FC = () => {
    const [gameParams, setGameParams] = useAtom(gameAtom);
    const setUser = useSetAtom(userAtom);
    const webApp = useTelegramWebApp();

    const [pops, setPops] = useState<PopSpec[]>([]);

    const lottieRef = useRef<LottieRefCurrentProps>(null);

    useEffect(() => {
        (async () => {
            console.log('gameParams', gameParams);
            if (gameParams.bubbles === null) {
                const roundData = await getCurrentRound();
                const shortRound = roundData.rounds.find((r) => r.round.round_type === 'short');
                if (shortRound) {
                    const vw = window.innerWidth;
                    const vh = window.innerHeight;
                    const now = Date.now();
                    const newBubbles = Array.from({length: 50}, (_, i) =>
                        createBubbleSpec(vw, vh, now + i, shortRound.round.id),
                    );
                    setGameParams((prev) => ({...prev, bubbles: [...newBubbles]}));
                }
            }
        })();
    }, [gameParams]);

    const handlePop = async (bubbleId: number) => {
        const bubble = gameParams.bubbles?.find((b) => b.id === bubbleId);
        if (!bubble) return;

        webApp?.HapticFeedback.impactOccurred('light');

        const animData = bubble.anim;
        if (!animData) {
            setGameParams((prev) => ({
                ...prev,
                bubbles: prev.bubbles?.filter((b) => b.id !== bubbleId) || [],
            }));
            return;
        }
        setPops((prev) => [
            ...prev,
            {
                size: bubble.size,
                top: bubble.top,
                left: bubble.left,
                data: animData,
                id: bubble.id,
                showScore: false,
            },
        ]);
        setGameParams((prev) => ({
            ...prev,
            bubbles: prev.bubbles?.filter((b) => b.id !== bubbleId) || [],
        }));
        if (bubble.roundId) {
            const result = await bonusPerRound({round_id: bubble.roundId});
            if (result.success) {
                setUser((prev) =>
                    prev
                        ? {
                              ...prev,
                              balance: prev.balance
                                  ? {
                                        ...prev.balance,
                                        coins_balance: prev.balance.coins_balance + result.bonus_info.amount,
                                    }
                                  : undefined,
                          }
                        : null,
                );
            }
        }
    };

    return (
        <>
            <BubbleLoading />
            <div className="absolute top-[50px] left-0 right-0 z-10 min-h-[calc(100vh-120px)] overflow-hidden">
                <div className="relative h-full w-full">
                    {gameParams.bubbles?.map((bubble, index) => (
                        <button
                            key={`bubble.id-${index}`}
                            aria-label="Pop bubble"
                            onClick={() => handlePop(bubble.id)}
                            style={{
                                position: 'absolute',
                                top: bubble.top,
                                left: bubble.left,
                                width: bubble.size,
                                height: bubble.size,
                                borderRadius: '9999px',
                                backgroundColor: bubble.fill,
                                border: `2px solid ${bubble.border}`,
                                boxShadow: '0 4px 8px rgba(0,0,0,0.25)',
                                cursor: 'pointer',
                            }}
                        />
                    ))}

                    {pops.map((pop) => (
                        <div
                            key={pop.id}
                            aria-hidden
                            style={{
                                position: 'absolute',
                                top: pop.top,
                                left: pop.left,
                                width: pop.size,
                                height: pop.size,
                                pointerEvents: 'none',
                                zIndex: 20,
                            }}
                        >
                            {!pop.showScore && (
                                <Lottie
                                    lottieRef={lottieRef}
                                    animationData={pop.data}
                                    loop={false}
                                    autoplay
                                    onComplete={() => {
                                        // Show +1 for 500ms after animation completes
                                        setPops((prev) =>
                                            prev.map((p) => (p.id === pop.id ? {...p, showScore: true} : p)),
                                        );
                                        setTimeout(() => {
                                            setPops((prev) => prev.filter((p) => p.id !== pop.id));
                                        }, 500);
                                    }}
                                    style={{width: '100%', height: '100%'}}
                                />
                            )}
                            {pop.showScore && (
                                <div className="absolute inset-0 flex items-center justify-center text-white text-title-1 select-none">
                                    +1
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
};
