import type {FC} from 'react';

type DefaultNotificationProps = {
    message: string;
};

export const DefaultNotification: FC<DefaultNotificationProps> = ({message}) => (
    <div className="flex gap-5 p-3 pr-10">
        <div className="h-8 w-8 flex items-center justify-center">
            <span className="text-3xl" aria-hidden>
                ⚡
            </span>
        </div>
        <div className="flex flex-col gap-2">
            <div className="txt-button-bold">{message}</div>
        </div>
    </div>
);
