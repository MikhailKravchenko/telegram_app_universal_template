export const getTimeWindow = () => {
    const now = new Date();
    const hourAgo = new Date(now.getTime() - 60 * 60 * 1000 * 2);
    return {nowISO: now.toISOString(), hourAgoISO: hourAgo.toISOString()};
};
