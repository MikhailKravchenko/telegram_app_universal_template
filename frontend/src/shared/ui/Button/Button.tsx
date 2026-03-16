import {type ButtonHTMLAttributes, type ReactNode} from 'react';
import {cn} from '@/shared/lib/utils/cn.ts';
import {useTranslation} from 'react-i18next';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    children: ReactNode;
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
}

export const Button = ({
    children,
    variant = 'primary',
    size = 'md',
    isLoading = false,
    className,
    disabled,
    ...props
}: ButtonProps) => {
    const {t} = useTranslation();
    const baseClasses =
        'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const variantClasses = {
        primary: 'bg-tg-button text-tg-button-text hover:opacity-80 focus:ring-tg-button',
        secondary: 'bg-tg-secondary-bg text-tg-text hover:opacity-80 focus:ring-tg-secondary-bg',
        outline:
            'border border-tg-button text-tg-button hover:bg-tg-button hover:text-tg-button-text focus:ring-tg-button',
        ghost: 'text-tg-link hover:bg-tg-secondary-bg focus:ring-tg-link',
    };

    const sizeClasses = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg',
    };

    return (
        <button
            className={cn(baseClasses, variantClasses[variant], sizeClasses[size], className)}
            disabled={disabled || isLoading}
            {...props}
        >
            {isLoading ? (
                <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                    </svg>
                    {t('common.loading')}
                </>
            ) : (
                children
            )}
        </button>
    );
};
