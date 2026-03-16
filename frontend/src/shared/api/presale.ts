import {http} from './http';
import {
    PresaleSchema,
    PresaleRoundInfoSchema,
    PresaleRoundStatsSchema,
    CreateDefaultRoundsResponseSchema,
    InvestmentSchema,
    CreateInvestmentRequestSchema,
    InvestmentSummarySchema,
    UserPresaleStatsSchema,
    PaginatedResponseSchema,
    InvestmentsQuerySchema,
    CurrentPresaleResponseSchema,
} from './schemas';
import type {z} from 'zod';

// Types
export type CurrentPresaleResponse = z.infer<typeof CurrentPresaleResponseSchema>;
export type Presale = z.infer<typeof PresaleSchema>;
export type PresaleRoundInfo = z.infer<typeof PresaleRoundInfoSchema>;
export type PresaleRoundStats = z.infer<typeof PresaleRoundStatsSchema>;
export type CreateDefaultRoundsResponse = z.infer<typeof CreateDefaultRoundsResponseSchema>;
export type Investment = z.infer<typeof InvestmentSchema>;
export type CreateInvestmentRequest = z.infer<typeof CreateInvestmentRequestSchema>;
export type InvestmentSummary = z.infer<typeof InvestmentSummarySchema>;
export type UserPresaleStats = z.infer<typeof UserPresaleStatsSchema>;
export type InvestmentsQuery = z.infer<typeof InvestmentsQuerySchema>;

// Presales API
export const getPresales = async () => {
    const response = await http.get('/presale/api/presales/');
    return PaginatedResponseSchema(PresaleSchema).parse(response);
};

export const getPresale = async (id: number): Promise<Presale> => {
    const response = await http.get(`/presale/api/presales/${id}/`);
    return PresaleSchema.parse(response);
};

export const getCurrentPresale = async (): Promise<CurrentPresaleResponse> => {
    const response = await http.get('/presale/api/presales/current/');
    return CurrentPresaleResponseSchema.parse(response);
};

// Presale Rounds API
export const getPresaleRoundInfo = async (presaleId: number, roundId: number): Promise<PresaleRoundInfo> => {
    const response = await http.get(`/presale/api/presales/${presaleId}/rounds/${roundId}/`);
    return PresaleRoundInfoSchema.parse(response);
};

export const getPresaleRoundsStats = async (presaleId: number): Promise<PresaleRoundStats> => {
    const response = await http.get(`/presale/api/presales/${presaleId}/rounds/stats/`);
    return PresaleRoundStatsSchema.parse(response);
};

export const getPresaleRounds = async (presaleId: number) => {
    const response = await http.get(`/presale/api/presales/${presaleId}/rounds/`);
    return PaginatedResponseSchema(PresaleRoundInfoSchema).parse(response);
};

export const createDefaultRounds = async (presaleId: number): Promise<CreateDefaultRoundsResponse> => {
    const response = await http.post(`/presale/api/presales/${presaleId}/rounds/create_default/`);
    return CreateDefaultRoundsResponseSchema.parse(response);
};

// Investments API
export const getInvestments = async (query?: InvestmentsQuery) => {
    const validatedQuery = query ? InvestmentsQuerySchema.parse(query) : {};
    const params = new URLSearchParams();

    Object.entries(validatedQuery).forEach(([key, value]) => {
        if (value !== undefined) {
            params.append(key, String(value));
        }
    });

    const url = `/presale/api/investments/${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await http.get(url);
    return PaginatedResponseSchema(InvestmentSchema).parse(response);
};

export const createInvestment = async (data: CreateInvestmentRequest): Promise<Investment> => {
    const validatedData = CreateInvestmentRequestSchema.parse(data);
    const response = await http.post('/presale/api/investments/', validatedData);
    return InvestmentSchema.parse(response);
};

export const getInvestment = async (id: number): Promise<Investment> => {
    const response = await http.get(`/presale/api/investments/${id}/`);
    return InvestmentSchema.parse(response);
};

export const getInvestmentSummary = async (): Promise<any> => {
    const response = await http.get('/presale/api/investments/summary/');
    return response;
};

export const getAllPresalesInvestments = async () => {
    const response = await http.get('/presale/api/investments/all_presales/');
    return PaginatedResponseSchema(InvestmentSchema).parse(response);
};

export const getUserPresaleStats = async (): Promise<UserPresaleStats> => {
    const response = await http.get('/presale/api/investments/user_stats/');
    return UserPresaleStatsSchema.parse(response);
};
