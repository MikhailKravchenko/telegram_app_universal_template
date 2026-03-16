import {z} from 'zod';

// Common schemas
export const PaginationSchema = z.object({
    count: z.number(),
    next: z.string().nullable(),
    previous: z.string().nullable(),
    page_size: z.number().optional(),
    total_pages: z.number().optional(),
});

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
    PaginationSchema.extend({
        results: z.array(itemSchema),
    });

export const ErrorResponseSchema = z.object({
    error: z.string(),
    detail: z.string().optional(),
    code: z.string().optional(),
});

// User schemas
export const UserSchema = z.object({
    id: z.number(),
    username: z.string(),
    telegram_id: z.string(),
    first_name: z.string(),
    last_name: z.string(),
});

export const BalanceSchema = z.object({
    coins_balance: z.number(),
    total_earned: z.number(),
    total_spent: z.number(),
    updated_at: z.string(),
});

export const UserInfoSchema = z.object({
    id: z.number(),
    username: z.string(),
    balance: BalanceSchema,
    telegram_id: z.string(),
    referral_count: z.number(),
});

export const TransactionSchema = z.object({
    id: z.number(),
    amount: z.number(),
    type: z.string(),
    description: z.string(),
    reference_id: z.string(),
    created_at: z.string(),
});

export const BonusSchema = z.object({
    id: z.number(),
    bonus_type: z.string(),
    bonus_type_display: z.string(),
    amount: z.number(),
    status: z.string(),
    status_display: z.string(),
    description: z.string(),
    expires_at: z.string().nullable(),
    created_at: z.string(),
    used_at: z.string().nullable(),
    can_be_used: z.boolean(),
    is_expired: z.boolean(),
});

// Auth schemas
export const TelegramLoginRequestSchema = z.object({
    telegramData: z.string().max(1000),
    referredBy: z.number().optional(),
});

export const TelegramLoginResponseSchema = z.object({
    access: z.string(),
    refresh: z.string(),
    user: UserSchema,
});

export const TelegramAuthStatusSchema = z.object({
    authenticated: z.boolean(),
    user_id: z.number(),
    username: z.string(),
});

export const LogoutResponseSchema = z.object({
    message: z.string(),
});

// Balance schemas
export const BalanceSummarySchema = z.object({
    current_balance: z.number(),
    total_earned: z.number(),
    total_spent: z.number(),
    net_earnings: z.number(),
    total_transactions: z.number(),
    positive_transactions: z.number(),
    negative_transactions: z.number(),
    last_updated: z.string(),
});

export const BonusStatisticsSchema = z.object({
    total_bonuses: z.number(),
    used_bonuses: z.number(),
    pending_bonuses: z.number(),
    active_bonuses: z.number(),
    expired_bonuses: z.number(),
    total_earned_from_bonuses: z.number(),
    bonus_types_stats: z.record(z.string(), z.any()),
    last_bonus: z.record(z.string(), z.any()).nullable(),
});

export const ClaimBonusResponseSchema = z.object({
    success: z.boolean(),
    message: z.string(),
    bonus: BonusSchema,
});

export const UseBonusResponseSchema = z.object({
    success: z.boolean(),
    message: z.string(),
    balance_updated: z.number(),
});

export const ActivityStatsSchema = z.object({
    daily_activity: z.record(z.string(), z.any()),
    weekly_activity: z.record(z.string(), z.any()),
    monthly_activity: z.record(z.string(), z.any()),
    total_activity: z.record(z.string(), z.any()),
});

// Referral schemas
export const ReferralBonusSchema = z.object({
    id: z.number(),
    referrer_username: z.string(),
    referred_username: z.string(),
    investment_amount: z.number(),
    bonus_amount: z.number(),
    bonus_percentage: z.number(),
    referral_level: z.number(),
    created_at: z.string(),
});

export const ReferralLevelSchema = z.object({
    id: z.number(),
    level: z.number(),
    min_referrals: z.number(),
    bonus_percentage: z.number(),
    is_active: z.boolean(),
    created_at: z.string(),
});

export const ReferralStatsLevelSchema = z.object({
    level: z.number(),
    min_referrals: z.number(),
    bonus_percentage: z.number(),
    referrals_needed: z.union([z.string(), z.number()]).nullable(),
});

export const ReferralSchema = z.object({
    user_id: z.number(),
    username: z.string().nullable(),
    joined_at: z.string(),
    total_bonus_earned: z.union([z.string(), z.number()]),
    last_bonus_at: z.string().nullable(),
});

export const ReferralStatsSchema = z.object({
    referrals_count: z.number(),
    total_bonuses_earned: z.number(),
    referral_link: z.string().nullable(),
    current_level: ReferralStatsLevelSchema.nullable(),
    next_level: ReferralStatsLevelSchema.nullable(),
    recent_bonuses: z.array(z.record(z.string(), z.any())),
    referrals: z.array(ReferralSchema),
});

export const ReferralLinkSchema = z.object({
    referral_link: z.string(),
    telegram_id: z.string(),
    user_id: z.number(),
});

export const GlobalReferralStatsSchema = z.object({
    total_referrals: z.number().optional(),
    total_bonuses_amount: z.number().optional(),
    total_bonuses_count: z.number().optional(),
    top_referrers: z.array(z.record(z.string(), z.any())).optional(),
    levels_distribution: z.array(z.record(z.string(), z.any())).optional(),
});

// Betting schemas
export const GameRoundSchema = z.object({
    id: z.number(),
    round_type: z.string(),
    start_time: z.string(),
    end_time: z.string(),
    status: z.string(),
    result: z.string().nullable(),
    pot_total: z.number(),
    pot_positive: z.number(),
    pot_negative: z.number(),
    fee_applied_rate: z.union([z.string(), z.number()]).nullable(),
    resolved_at: z.string().nullable(),
    news_title: z.string().optional(),
    news_content: z.string().optional(),
    news_image_url: z.string().nullable().optional(),
    bets_count: z.number(),
    time_remaining: z.number(),
    can_bet: z.boolean(),
});

export const RoundSettingsSchema = z.object({
    id: z.number(),
    round_duration_seconds: z.number(),
    platform_fee_rate: z.union([z.string(), z.number()]),
    min_bet: z.number(),
    max_bet: z.number(),
    news_freshness_minutes: z.number(),
    min_news_content_length: z.number(),
    enabled: z.boolean(),
});

export const CurrentRoundResponseSchema = z.object({
    rounds: z.array(
        z.object({
            round: GameRoundSchema,
            user_bet: z.record(z.string(), z.any()).nullable(),
            can_place_bet: z.boolean(),
        }),
    ),
    settings: RoundSettingsSchema,
});

export const BonusPerRoundRequestSchema = z.object({
    round_id: z.number(),
});

export const BonusInfoSchema = z.object({
    bonus_id: z.number(),
    amount: z.number(),
    type: z.string(),
    description: z.string(),
});

export const BonusPerRoundResponseSchema = z.object({
    success: z.boolean(),
    message: z.string(),
    bonus_info: BonusInfoSchema,
});

export const BetSchema = z.object({
    id: z.number(),
    user: z.number(),
    username: z.string().nullable(),
    round: z.number(),
    round_status: z.string(),
    round_result: z.string().nullable(),
    amount: z.number(),
    choice: z.string(),
    status: z.string(),
    payout_amount: z.number(),
    payout_coefficient: z.union([z.string(), z.number()]).nullable(),
    created_at: z.string(),
    news_title: z.string().nullable().optional(),
    news_content: z.string().nullable().optional(),
    news_image_url: z.string().nullable().optional(),
    bets_count: z.number(),
    pot_total: z.union([z.string(), z.number()]),
});

export const CreateBetRequestSchema = z.object({
    round: z.number(),
    amount: z.number(),
    choice: z.enum(['positive', 'negative']),
});

export const CreateBetResponseSchema = z.object({
    id: z.number(),
    user: z.number(),
    round: z.number(),
    amount: z.number(),
    choice: z.string(),
    status: z.string(),
    created_at: z.string(),
});

export const NewsSchema = z.object({
    id: z.number(),
    title: z.string(),
    content: z.string(),
    image_url: z.string(),
    source_url: z.string(),
    category: z.string(),
    language: z.string(),
    created_at: z.string(),
});

// Presale schemas
export const PresaleSchema = z.object({
    id: z.number(),
    name: z.string(),
    status: z.string(),
    current_round: z.number(),
    total_rounds: z.number(),
    total_invested: z.number(),
    total_tokens_sold: z.union([z.string(), z.number()]),
    current_rate: z.union([z.string(), z.number()]),
    current_round_investment: z.number(),
    current_round_target: z.number(),
    progress_percent: z.number(),
    start_time: z.string(),
    end_time: z.string().nullable(),
    created_at: z.string(),
    updated_at: z.string(),
});

export const PresaleRoundInfoSchema = z.object({
    round_number: z.number(),
    tokens_per_coin: z.number(),
    target_investment: z.number(),
    current_investment: z.number(),
    progress_percent: z.number(),
    remaining_investment: z.number(),
    is_completed: z.boolean(),
});

export const CurrentPresaleResponseSchema = z.object({
    id: z.number(),
    name: z.string(),
    status: z.string(),
    current_round: z.number(),
    total_rounds: z.number(),
    total_invested: z.number(),
    total_tokens_sold: z.union([z.string(), z.number()]),
    start_time: z.string(),
    end_time: z.string().nullable(),
    current_round_info: PresaleRoundInfoSchema,
});

export const PresaleRoundStatsSchema = z.object({
    round_number: z.number(),
    total_invested: z.number(),
    total_tokens: z.number(),
    investors_count: z.number(),
    target_investment: z.number(),
    progress_percent: z.number(),
    rate: z.number(),
    is_current: z.boolean(),
    is_completed: z.boolean(),
});

export const PresaleRoundSchema = z.object({
    round_number: z.number(),
    tokens_per_coin: z.number(),
    target_investment: z.number(),
    is_active: z.boolean(),
    created_at: z.string(),
});

export const CreateDefaultRoundsResponseSchema = z.object({
    created_count: z.number(),
    rounds: z.array(z.record(z.string(), z.any())),
});

export const InvestmentSchema = z.object({
    id: z.number(),
    user: z.number(),
    user_username: z.string(),
    presale: z.number(),
    amount: z.number(),
    tokens_received: z.union([z.string(), z.number()]),
    round_number: z.number(),
    rate_at_purchase: z.union([z.string(), z.number()]),
    transaction_id: z.string().nullable(),
    created_at: z.string(),
});

export const CreateInvestmentRequestSchema = z.object({
    amount: z.number().min(10).max(1000000),
});

export const InvestmentSummarySchema = z.object({
    total_invested: z.union([z.string(), z.number()]),
    total_tokens: z.union([z.string(), z.number()]),
    investments_count: z.union([z.string(), z.number()]),
    average_rate: z.union([z.string(), z.number()]),
    first_investment: z.record(z.string(), z.any()).nullable(),
    last_investment: z.record(z.string(), z.any()).nullable(),
});

export const PresaleInvestmentSchema = z.object({
    presale_id: z.number(),
    presale_name: z.string(),
    total_invested: z.number(),
    total_tokens: z.number(),
    investments_count: z.number(),
    first_investment_at: z.string(),
    last_investment_at: z.string(),
});

export const UserPresaleStatsSchema = z.object({
    user: z.number(),
    user_username: z.string(),
    total_invested: z.number(),
    total_tokens: z.number(),
    investments_count: z.number(),
    first_investment_at: z.string(),
    last_investment_at: z.string(),
    updated_at: z.string(),
});

export const LeaderboardEntrySchema = z.object({
    user: z.number(),
    user_username: z.string(),
    total_invested: z.number(),
    total_tokens: z.number(),
    investments_count: z.number(),
    rank: z.number(),
});

export const GlobalPresaleStatsSchema = z.object({
    total_presales: z.number(),
    active_presales: z.number(),
    total_investments: z.number(),
    total_invested: z.number(),
    total_tokens_sold: z.number(),
    average_investment: z.number(),
    unique_investors: z.number(),
});

// Query parameter schemas
export const GameRoundsQuerySchema = z.object({
    status: z.enum(['open', 'closed', 'finished', 'void']).optional(),
    start_time_from: z.string().optional(),
    start_time_to: z.string().optional(),
    search: z.string().optional(),
    ordering: z.enum(['start_time', 'end_time', 'status']).optional(),
    page: z.number().optional(),
    page_size: z.number().max(100).optional(),
});

export const BetsQuerySchema = z.object({
    choice: z.enum(['positive', 'negative']).optional(),
    status: z.enum(['pending', 'won', 'lost', 'refunded']).optional(),
    amount_from: z.number().optional(),
    amount_to: z.number().optional(),
    created_at_from: z.string().optional(),
    created_at_to: z.string().optional(),
    ordering: z.string().optional(),
    page: z.number().optional(),
    page_size: z.number().optional(),
});

export const NewsQuerySchema = z.object({
    page: z.number().optional(),
    page_size: z.number().max(100).optional(),
});

export const InvestmentsQuerySchema = z.object({
    page: z.number().optional(),
    page_size: z.number().optional(),
});

export const LeaderboardQuerySchema = z.object({
    limit: z.number().optional(),
});
