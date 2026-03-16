import {useTranslation} from 'react-i18next';
import {Icon} from '@/components/Icon';

interface SidebarItemProps {
    icon: Parameters<typeof Icon>[0]['name'];
    label: string;
    comingSoon?: boolean;
}

export const SidebarItem = ({icon, label, comingSoon}: SidebarItemProps) => {
    const {t} = useTranslation();
    return (
        <div className="flex items-center gap-4 px-3 py-3 text-left">
            <Icon name={icon} size={24} />
            <span className={`txt-headline ${!comingSoon ? 'text-[var(--accent)]' : 'text-[var(--charcoal-grey)]'}`}>
                {label}
            </span>
            {comingSoon && (
                <span className="px-2 py-0.5 rounded-full border border-stone-700 text-[var(--charcoal-grey)] txt-caption">
                    {t('common.comingSoon')}
                </span>
            )}
        </div>
    );
};
