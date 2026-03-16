import ArrowLeft from './arrow-left.svg?react';
import ArrowRight from './arrow-right.svg?react';
import Check from './check.svg?react';
import ChevronRight from './chevron-right.svg?react';
import Close from './close.svg?react';
import Coins from './coins.svg?react';
import Forecasts from './forecasts.svg?react';
import Game from './game.svg?react';
import More from './more.svg?react';
import Octahedron from './octahedron.svg?react';
import Presale from './presale.svg?react';
import Result from './result.svg?react';
import SquareRoundedCheck from './square-rounded-check.svg?react';
import Star from './star.svg?react';
import Tasks from './tasks.svg?react';
import News from './news.svg?react';
import Card from './card.svg?react';
import Charity from './charity.svg?react';
import Help from './help.svg?react';
import Profile from './profile.svg?react';
import Rules from './rules.svg?react';
import Vpn from './vpn.svg?react';
import Wallet from './wallet.svg?react';
import ThumbUp from './thumb-up.svg?react';
import ThumbDown from './thumb-down.svg?react';
import Timer from './timer.svg?react';
import X from './x.svg?react';
import Telegram from './telegram.svg?react';
import Users from './users.svg?react';
import Refresh from './refresh.svg?react';

export const iconsMap = {
    arrowLeft: ArrowLeft,
    arrowRight: ArrowRight,
    check: Check,
    chevronRight: ChevronRight,
    close: Close,
    coins: Coins,
    forecasts: Forecasts,
    game: Game,
    more: More,
    octahedron: Octahedron,
    presale: Presale,
    result: Result,
    squareRoundedCheck: SquareRoundedCheck,
    star: Star,
    tasks: Tasks,
    news: News,
    card: Card,
    charity: Charity,
    help: Help,
    profile: Profile,
    rules: Rules,
    vpn: Vpn,
    wallet: Wallet,
    thumbUp: ThumbUp,
    thumbDown: ThumbDown,
    timer: Timer,
    x: X,
    telegram: Telegram,
    users: Users,
    refresh: Refresh,
} as const;

export type TIconMapKeys = keyof typeof iconsMap;
