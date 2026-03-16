import {type FC, type PropsWithChildren, useEffect, useRef} from 'react';
import {useSetAtom} from 'jotai';
import {bettingRoundsWS, onMessage} from '@/shared/ws';
import {gameAtom} from '@/atom/gameAtom.ts';
import {RoundFinishedNotification} from '@/features/forecast';
import {useFlashMessage} from '@/components/FlashMessage';
import {createBubbleSpec} from '@/features/bubble-game';

export const GameProvider: FC<PropsWithChildren> = ({children}) => {
    const mounted = useRef(false);
    const setGameParams = useSetAtom(gameAtom);
    const {setFlashMessage} = useFlashMessage();

    useEffect(() => {
        if (!mounted.current) {
            mounted.current = true;
            bettingRoundsWS.connect();
        }

        const offMessage = onMessage((msg) => {
            if (msg?.status === 'open') {
                const vw = window.innerWidth;
                const vh = window.innerHeight;
                const now = Date.now();
                const newBubbles = Array.from({length: 50}, (_, i) => createBubbleSpec(vw, vh, now + i, msg.id));
                setGameParams((prev) => {
                    const prevBubbles = prev.bubbles ?? [];
                    if (prevBubbles.length >= 300) {
                        return prev;
                    }
                    const remaining = 300 - prevBubbles.length;
                    const toAdd = remaining >= newBubbles.length ? newBubbles : newBubbles.slice(0, remaining);
                    return {
                        ...prev,
                        bubbles: [...prevBubbles, ...toAdd],
                    };
                });
            } else if (msg?.status === 'finished') {
                setFlashMessage({
                    component: <RoundFinishedNotification />,
                });
            }
        });

        return () => {
            offMessage();
        };
    }, []);

    return children;
};
