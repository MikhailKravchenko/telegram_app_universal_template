import {http} from './http';
import {
    TelegramLoginRequestSchema,
    TelegramLoginResponseSchema,
    TelegramAuthStatusSchema,
    LogoutResponseSchema,
    UserInfoSchema,
    BalanceSchema,
    BalanceSummarySchema,
    TransactionSchema,
    BonusSchema,
    BonusStatisticsSchema,
    ClaimBonusResponseSchema,
    UseBonusResponseSchema,
    ActivityStatsSchema,
    ReferralStatsSchema,
    ReferralLinkSchema,
    ReferralBonusSchema,
    ReferralLevelSchema,
    GlobalReferralStatsSchema,
    PaginatedResponseSchema,
    ReferralSchema,
} from './schemas';
import {z} from 'zod';

// Types
export type TelegramLoginRequest = z.infer<typeof TelegramLoginRequestSchema>;
export type TelegramLoginResponse = z.infer<typeof TelegramLoginResponseSchema>;
export type TelegramAuthStatus = z.infer<typeof TelegramAuthStatusSchema>;
export type LogoutResponse = z.infer<typeof LogoutResponseSchema>;
export type UserInfo = z.infer<typeof UserInfoSchema>;
export type Balance = z.infer<typeof BalanceSchema>;
export type BalanceSummary = z.infer<typeof BalanceSummarySchema>;
export type Transaction = z.infer<typeof TransactionSchema>;
export type Bonus = z.infer<typeof BonusSchema>;
export type BonusStatistics = z.infer<typeof BonusStatisticsSchema>;
export type ClaimBonusResponse = z.infer<typeof ClaimBonusResponseSchema>;
export type UseBonusResponse = z.infer<typeof UseBonusResponseSchema>;
export type ActivityStats = z.infer<typeof ActivityStatsSchema>;
export type ReferralStats = z.infer<typeof ReferralStatsSchema>;
export type ReferralLink = z.infer<typeof ReferralLinkSchema>;
export type ReferralBonus = z.infer<typeof ReferralBonusSchema>;
export type ReferralLevel = z.infer<typeof ReferralLevelSchema>;
export type GlobalReferralStats = z.infer<typeof GlobalReferralStatsSchema>;
export type Referral = z.infer<typeof ReferralSchema>;

// Authentication API
export const telegramLogin = async (data: TelegramLoginRequest): Promise<TelegramLoginResponse> => {
    const validatedData = TelegramLoginRequestSchema.parse(data);
    const response = await http.post('/accounts/telegram/login/', validatedData);
    return TelegramLoginResponseSchema.parse(response);
};

export const getTelegramAuthStatus = async (): Promise<TelegramAuthStatus> => {
    const response = await http.get('/accounts/telegram/status/');
    return TelegramAuthStatusSchema.parse(response);
};

export const logout = async (): Promise<LogoutResponse> => {
    const response = await http.post('/accounts/logout/');
    return LogoutResponseSchema.parse(response);
};

// User API
export const getUserInfo = async (id?: number): Promise<UserInfo> => {
    const url = id ? `/accounts/users/${id}/` : '/accounts/users/';
    const response = await http.get(url);

    if (Array.isArray(response)) {
        const arr = z.array(UserInfoSchema).parse(response);
        if (arr.length === 0) {
            throw new Error('User not found');
        }
        return arr[0];
    }

    return UserInfoSchema.parse(response);
};

// Balance API
export const getUserBalance = async (id?: number): Promise<Balance> => {
    const url = id ? `/accounts/balances/${id}/` : '/accounts/balances/';
    const response = await http.get(url);
    return BalanceSchema.parse(response);
};

export const getBalanceSummary = async (): Promise<BalanceSummary> => {
    const response = await http.get('/accounts/balance-summary/');
    return BalanceSummarySchema.parse(response);
};

// Transactions API
export const getTransactions = async (): Promise<Transaction[]> => {
    const response = await http.get('/accounts/transactions/');
    return PaginatedResponseSchema(TransactionSchema).parse(response).results;
};

export const getTransaction = async (id: number): Promise<Transaction> => {
    const response = await http.get(`/accounts/transactions/${id}/`);
    return TransactionSchema.parse(response);
};

// Bonuses API
export const getBonuses = async (): Promise<Bonus[]> => {
    const response = await http.get('/accounts/bonuses/');
    return PaginatedResponseSchema(BonusSchema).parse(response).results;
};

export const getBonus = async (id: number): Promise<Bonus> => {
    const response = await http.get(`/accounts/bonuses/${id}/`);
    return BonusSchema.parse(response);
};

export const getBonusStatistics = async (): Promise<BonusStatistics> => {
    const response = await http.get('/accounts/bonuses/statistics/');
    return BonusStatisticsSchema.parse(response);
};

export const claimDailyBonus = async (): Promise<ClaimBonusResponse> => {
    const response = await http.post('/accounts/bonuses/claim_daily/');
    return ClaimBonusResponseSchema.parse(response);
};

export const claimSocialBonus = async (): Promise<ClaimBonusResponse> => {
    const response = await http.post('/accounts/bonuses/claim_social/');
    return ClaimBonusResponseSchema.parse(response);
};

export const claimTelegramChannel1Bonus = async (): Promise<ClaimBonusResponse> => {
    const response = await http.post('/accounts/bonuses/claim_telegram_channel_1/');
    return ClaimBonusResponseSchema.parse(response);
};

export const claimTelegramChannel2Bonus = async (): Promise<ClaimBonusResponse> => {
    const response = await http.post('/accounts/bonuses/claim_telegram_channel_2/');
    return ClaimBonusResponseSchema.parse(response);
};

export const useBonus = async (id: number): Promise<UseBonusResponse> => {
    const response = await http.post(`/accounts/bonuses/${id}/use/`);
    return UseBonusResponseSchema.parse(response);
};

export const getActivityStats = async (): Promise<ActivityStats> => {
    const response = await http.get('/accounts/bonuses/activity_stats/');
    return ActivityStatsSchema.parse(response);
};

// Referrals API
export const getReferralStats = async (): Promise<any> => {
    const response = await http.get('/accounts/referrals/my-stats/');
    return response;
};

export const getReferralLink = async (): Promise<ReferralLink> => {
    const response = await http.get('/accounts/referrals/my-link/');
    return ReferralLinkSchema.parse(response);
};

export const getReferralBonuses = async (): Promise<ReferralBonus[]> => {
    const response = await http.get('/accounts/referrals/my-bonuses/');
    return PaginatedResponseSchema(ReferralBonusSchema).parse(response).results;
};

// Paginated version for UI that needs pagination controls
export type PaginatedReferralBonuses = {
    count: number;
    next: string | null;
    previous: string | null;
    page_size?: number;
    total_pages?: number;
    results: ReferralBonus[];
};

export const getReferralBonusesPage = async (page: number = 1, page_size: number = 10): Promise<ReferralBonus[]> => {
    const response = await http.get(`/accounts/referrals/my-bonuses/?page=${page}&page_size=${page_size}`);
    return z.array(ReferralBonusSchema).parse(response);
};

export const getReferralLevels = async (): Promise<ReferralLevel[]> => {
    const response = await http.get('/accounts/referrals/levels/');
    return PaginatedResponseSchema(ReferralLevelSchema).parse(response).results;
};

export const getGlobalReferralStats = async (): Promise<GlobalReferralStats> => {
    const response = await http.get('/accounts/referrals/global-stats/');
    return GlobalReferralStatsSchema.parse(response);
};
