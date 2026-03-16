import {Icon} from '@/components/Icon';
import {useTranslation} from 'react-i18next';
import type {TIconMapKeys} from '@/assets/icons';
import {CheckBadge} from './CheckBadge';

interface TaskItemProps {
    title: string;
    icon: TIconMapKeys;
    amount?: number;
    onComplete?: () => void;
    completed?: boolean;
}

export const TaskCard = ({title, icon, completed, amount, onComplete}: TaskItemProps) => {
    const {t} = useTranslation();

    return (
        <div className="w-full rounded-[20px] border border-[var(--coffee-brown)] p-2 flex items-center justify-between">
            {/* Left */}
            <div className="flex gap-4 items-center pr-2 flex-1 min-w-0">
                <div className="w-14 p-4 rounded-[12px] overflow-hidden">
                    <Icon name={icon} stroke="var(--charcoal-grey)" />
                </div>
                <div className="flex flex-col gap-1 justify-center min-w-0">
                    <p className="txt-subhead text-white break-words">{title}</p>
                    {amount && (
                        <div className="flex items-center gap-2">
                            <Icon name="coins" size={24} stroke="var(--accent)" />
                            <span className="txt-button-bold text-[var(--accent)]">+{amount}</span>
                        </div>
                    )}
                </div>
            </div>
            {/* Right button */}
            {completed ? (
                <CheckBadge />
            ) : (
                <button
                    onClick={onComplete}
                    className="h-10 rounded-[14px] border border-[var(--accent)] bg-[#65210A] px-3 txt-button-bold text-white"
                >
                    {t('common.complete')}
                </button>
            )}
        </div>
    );
};
