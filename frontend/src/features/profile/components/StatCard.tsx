export const StatCard = ({label, value}: {label: string; value?: string | number}) => (
    <div className="min-w-[150px] flex-1 rounded-[12px] border border-[var(--coffee-brown)] p-4 flex flex-col gap-1">
        <div className="txt-footnote text-[var(--charcoal-grey)]">{label}</div>
        <div className="txt-title-2 text-[var(--accent)]">{value ?? '—'}</div>
    </div>
);
