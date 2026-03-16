export const formatNumber = (n: string | number | undefined) => {
    if (typeof n !== 'number') {
        n = Number(n);
    }
    if (n < 1000) return String(n);
    if (n < 1000000) return `${(n / 1000).toFixed(1)}K`;
    if (n < 1000000000) return `${(n / 1000000).toFixed(1)}M`;
    return `${(n / 1000000000).toFixed(1)}B`;
};
