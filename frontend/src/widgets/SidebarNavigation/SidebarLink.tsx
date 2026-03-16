import {Link} from '@tanstack/react-router';
import {Icon} from '@/components/Icon';

interface SidebarLinkProps {
    icon: Parameters<typeof Icon>[0]['name'];
    label: string;
    to: string;
    onClose: () => void;
}

export const SidebarLink = ({icon, label, to, onClose}: SidebarLinkProps) => (
    <Link to={to} onClick={onClose} className="w-full flex items-center gap-4 px-3 py-3 text-left">
        <Icon name={icon} size={24} />
        <span className="txt-headline text-[var(--accent)]">{label}</span>
    </Link>
);
