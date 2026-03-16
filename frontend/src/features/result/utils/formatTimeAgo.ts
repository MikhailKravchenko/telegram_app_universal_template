export const formatTimeAgo = (iso?: string | null) => {
    if (!iso) return '';
    const target = new Date(iso).getTime();
    const diffMs = Date.now() - target;
    if (!Number.isFinite(diffMs)) return '';
    const sec = Math.max(0, Math.floor(diffMs / 1000));
    const min = Math.floor(sec / 60);
    const hr = Math.floor(min / 60);
    if (hr > 0) return `${hr} hrs ago`;
    if (min > 0) return `${min} mins ago`;
    return 'just now';
};
