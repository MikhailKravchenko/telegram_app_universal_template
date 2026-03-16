import {getInitials} from '../utils/getInitials.ts';

export const FriendRow = ({index, name}: {index: number; name: string}) => (
    <div className="w-full px-3 py-1 rounded-[4px] flex items-center justify-between">
        <div className="flex-1 min-w-0 flex items-center gap-3">
            <div className="w-[36px] txt-body text-[var(--charcoal-grey)]">{index}</div>
            <div className="flex items-center gap-3">
                <div className="w-[42px] h-[42px] rounded-full bg-gradient-to-b from-[#aad5ff] via-[#94c4f3] to-[#81b5e9] flex items-center justify-center">
                    <div className="txt-button-bold text-white text-[14px]">{getInitials(name)}</div>
                </div>
                <div className="txt-body truncate">{name}</div>
            </div>
        </div>
    </div>
);
