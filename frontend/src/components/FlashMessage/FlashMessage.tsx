import {type FC, type PropsWithChildren, useEffect, useState} from 'react';
import {useFlashMessage} from './context/FlashMessageContext';
import {Icon} from '@/components/Icon';

const FlashMessage: FC<PropsWithChildren> = ({children}) => {
    const {flashMessage, setFlashMessage} = useFlashMessage();
    const [progress, setProgress] = useState(100);
    const timerMs = 10000;

    useEffect(() => {
        if (flashMessage) {
            const timer = setTimeout(() => setFlashMessage(null), timerMs);
            const interval = setInterval(() => {
                setProgress((prevProgress) => Math.max(0, prevProgress - 1));
            }, timerMs / 100);
            return () => {
                clearTimeout(timer);
                clearInterval(interval);
            };
        }
    }, [flashMessage, setFlashMessage]);

    useEffect(() => {
        if (!flashMessage) {
            setProgress(100);
        }
    }, [flashMessage]);

    const handleClose = () => {
        setFlashMessage(null);
    };

    return (
        <>
            {flashMessage && (
                <div className="absolute bottom-[120px] left-0 right-0 z-[9999]">
                    <div className="mx-4 flex justify-center">
                        <div
                            role="status"
                            aria-live="polite"
                            className="relative w-full max-w-[360px] rounded-[10px] border border-[var(--accent)] bg-[rgba(0,0,0,0.9)] text-white shadow-[0_12px_24px_rgba(228,81,37,0.25)] overflow-hidden"
                        >
                            <button
                                type="button"
                                onClick={handleClose}
                                aria-label="Close"
                                className="absolute right-3 top-3 p-1 text-white/80 hover:text-white"
                            >
                                <Icon name="close" size={20} />
                            </button>
                            {flashMessage.component || null}
                            <div
                                className="absolute bottom-0 left-0 h-[3px] bg-[var(--accent)]"
                                style={{width: `${progress}%`}}
                            />
                        </div>
                    </div>
                </div>
            )}
            {children}
        </>
    );
};

export default FlashMessage;
