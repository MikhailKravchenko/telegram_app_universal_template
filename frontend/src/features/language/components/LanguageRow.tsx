import {FlagIcon, type LanguageCode} from '@/shared/ui';
import {Icon} from '@/components/Icon';

interface LanguageRowProps {
    language: {
        code: LanguageCode;
        name: string;
        translationKey: string;
    };
    isSelected: boolean;
    onSelect: () => void;
}

export const LanguageRow = ({language, isSelected, onSelect}: LanguageRowProps) => {
    return (
        <button type="button" onClick={onSelect} className="flex gap-4 items-center px-8 py-4 justify-between">
            <div className="flex gap-4 items-center">
                <FlagIcon language={language.code} className="w-6 h-4" />
                <span className={`txt-headline ${isSelected ? 'text-[var(--accent)]' : 'text-white'}`}>
                    {language.name}
                </span>
            </div>
            <div className="overflow-hidden relative size-6">
                {isSelected && <Icon name="check" size={24} stroke="var(--accent)" />}
            </div>
        </button>
    );
};
