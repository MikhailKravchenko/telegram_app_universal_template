// Example usage of the API functions
// This file demonstrates how to use the implemented API functions

import {
    // Authentication
    telegramLogin,
    getTelegramAuthStatus,

    // User & Balance
    getUserInfo,
    getUserBalance,
    getBalanceSummary,

    // Transactions & Bonuses
    getTransactions,
    getBonuses,
    claimDailyBonus,
    claimSocialBonus,

    // Referrals
    getReferralStats,
    getReferralLink,

    // Betting
    getGameRounds,
    getCurrentRound,
    createBet,
    getBets,
    getNews,

    // Presale
    getPresales,
    getCurrentPresale,
    getInvestments,
    createInvestment,

    // Types
    type TelegramLoginRequest,
    type CreateBetRequest,
    type CreateInvestmentRequest,
} from '@/shared/api';

// Example: Authentication flow
export const exampleAuthFlow = async () => {
    try {
        // Login with Telegram data
        const loginData: TelegramLoginRequest = {
            telegramData: 'telegram_auth_data_string',
            referredBy: 123, // optional
        };

        const loginResponse = await telegramLogin(loginData);
        console.log('Login successful:', loginResponse.user);

        // Check auth status
        const authStatus = await getTelegramAuthStatus();
        console.log('Auth status:', authStatus);

        // Get user info
        const userInfo = await getUserInfo();
        console.log('User info:', userInfo);
    } catch (error) {
        console.error('Auth error:', error);
    }
};

// Example: Balance and transactions
export const exampleBalanceFlow = async () => {
    try {
        // Get user balance
        const balance = await getUserBalance();
        console.log('Balance:', balance);

        // Get balance summary
        const summary = await getBalanceSummary();
        console.log('Balance summary:', summary);

        // Get transactions
        const transactions = await getTransactions();
        console.log('Transactions:', transactions);
    } catch (error) {
        console.error('Balance error:', error);
    }
};

// Example: Bonuses
export const exampleBonusFlow = async () => {
    try {
        // Get available bonuses
        const bonuses = await getBonuses();
        console.log('Available bonuses:', bonuses);

        // Claim daily bonus
        const dailyBonus = await claimDailyBonus();
        console.log('Daily bonus claimed:', dailyBonus);

        // Claim social bonus
        const socialBonus = await claimSocialBonus();
        console.log('Social bonus claimed:', socialBonus);
    } catch (error) {
        console.error('Bonus error:', error);
    }
};

// Example: Betting
export const exampleBettingFlow = async () => {
    try {
        // Get current round
        const currentRound = await getCurrentRound();
        console.log('Current round:', currentRound);

        // Get game rounds with filters
        const rounds = await getGameRounds({
            status: 'open',
            page: 1,
            page_size: 10,
        });
        console.log('Game rounds:', rounds);

        // Create a bet
        const betData: CreateBetRequest = {
            round: 1,
            amount: 100,
            choice: 'positive',
        };

        const newBet = await createBet(betData);
        console.log('Bet created:', newBet);

        // Get user bets
        const userBets = await getBets({
            status: 'pending',
            page: 1,
        });
        console.log('User bets:', userBets);

        // Get news
        const news = await getNews({page: 1});
        console.log('News:', news);
    } catch (error) {
        console.error('Betting error:', error);
    }
};

// Example: Presale and investments
export const examplePresaleFlow = async () => {
    try {
        // Get current presale
        const currentPresale = await getCurrentPresale();
        console.log('Current presale:', currentPresale);

        // Get all presales
        const presales = await getPresales();
        console.log('All presales:', presales);

        // Create investment
        const investmentData: CreateInvestmentRequest = {
            amount: 500,
        };

        const newInvestment = await createInvestment(investmentData);
        console.log('Investment created:', newInvestment);

        // Get user investments
        const investments = await getInvestments();
        console.log('User investments:', investments);
    } catch (error) {
        console.error('Presale error:', error);
    }
};

// Example: Referrals
export const exampleReferralFlow = async () => {
    try {
        // Get referral stats
        const stats = await getReferralStats();
        console.log('Referral stats:', stats);

        // Get referral link
        const link = await getReferralLink();
        console.log('Referral link:', link);
    } catch (error) {
        console.error('Referral error:', error);
    }
};
