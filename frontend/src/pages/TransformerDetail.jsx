import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import TransformerAnalyticsTab from '../components/TransformerAnalyticsTab';
import { getTransformer } from '../api/client';

const RISK_COLOR = {
    LOW: '#16a34a',
    MEDIUM: '#ca8a04',
    HIGH: '#ea580c',
    CRITICAL: '#dc2626',
    UNKNOWN: '#718096',
};

function DetailSkeleton() {
    return (
        <div className="flex h-full flex-col gap-4 p-6">
            <div className="h-24 animate-pulse rounded-lg bg-slate-900" />
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-4">
                <div className="h-24 animate-pulse rounded-lg bg-slate-900" />
                <div className="h-24 animate-pulse rounded-lg bg-slate-900" />
                <div className="h-24 animate-pulse rounded-lg bg-slate-900" />
                <div className="h-24 animate-pulse rounded-lg bg-slate-900" />
            </div>
            <div className="h-96 animate-pulse rounded-lg bg-slate-900" />
        </div>
    );
}

function StatCard({ label, value, color = '#e2e8f0' }) {
    return (
        <div className="rounded-lg border border-slate-800 bg-[#13151f] px-4 py-3">
            <div className="mb-1 text-[11px] font-medium uppercase tracking-normal text-slate-500">{label}</div>
            <div className="text-xl font-bold" style={{ color }}>{value}</div>
        </div>
    );
}

function TabButton({ active, children, onClick }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`rounded-md border px-3 py-2 text-xs font-semibold transition ${
                active
                    ? 'border-sky-500 bg-sky-500/10 text-sky-300'
                    : 'border-slate-800 bg-[#13151f] text-slate-400 hover:bg-slate-800 hover:text-slate-100'
            }`}
        >
            {children}
        </button>
    );
}

function OverviewTab({ transformer, prediction }) {
    return (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_360px]">
            <section className="rounded-lg border border-slate-800 bg-[#13151f] p-4">
                <h2 className="text-sm font-semibold text-slate-100">Transformer Profile</h2>
                <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <StatCard label="Transformer ID" value={transformer.transformer_id} color="#60a5fa" />
                    <StatCard label="Substation" value={transformer.substation_name} />
                    <StatCard label="District" value={transformer.district} />
                    <StatCard label="Capacity" value={`${transformer.capacity_kva} kVA`} />
                    <StatCard label="Installation year" value={transformer.installation_year} />
                    <StatCard label="Location" value={`${transformer.latitude}, ${transformer.longitude}`} />
                </div>
            </section>

            <section className="rounded-lg border border-slate-800 bg-[#13151f] p-4">
                <h2 className="text-sm font-semibold text-slate-100">AI Risk Summary</h2>
                {prediction ? (
                    <div className="mt-4 space-y-3">
                        <StatCard label="Health score" value={prediction.health_score} color={RISK_COLOR[prediction.risk_level] || '#e2e8f0'} />
                        <StatCard label="30-day failure probability" value={`${(prediction.failure_probability_30d * 100).toFixed(0)}%`} color={RISK_COLOR[prediction.risk_level] || '#e2e8f0'} />
                        <StatCard label="Anomaly detected" value={prediction.anomaly_detected ? 'YES' : 'NO'} color={prediction.anomaly_detected ? '#dc2626' : '#16a34a'} />
                    </div>
                ) : (
                    <div className="mt-4 rounded-lg border border-dashed border-slate-800 bg-[#0f1117] p-5 text-sm text-slate-500">
                        No prediction is available for this transformer.
                    </div>
                )}
            </section>
        </div>
    );
}

export default function TransformerDetail() {
    const { transformer_id } = useParams();
    const transformerId = decodeURIComponent(transformer_id || '');
    const navigate = useNavigate();
    const [detail, setDetail] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        let active = true;

        getTransformer(transformerId)
            .then((response) => {
                if (!active) return;
                setError('');
                setDetail(response.data);
            })
            .catch((err) => {
                if (!active) return;
                setDetail(null);
                setError(err.response?.status === 404 ? 'Transformer not found.' : 'Unable to load transformer details.');
            })
            .finally(() => {
                if (active) setLoading(false);
            });

        return () => {
            active = false;
        };
    }, [transformerId]);

    if (loading) return <DetailSkeleton />;

    if (error || !detail?.transformer) {
        return (
            <div className="p-6">
                <button type="button" onClick={() => navigate('/')} className="mb-4">
                    Back to dashboard
                </button>
                <div className="rounded-lg border border-rose-900/70 bg-rose-950/30 p-4 text-sm font-medium text-rose-300">
                    {error || 'Transformer not found.'}
                </div>
            </div>
        );
    }

    const transformer = detail.transformer;
    const prediction = detail.latest_prediction;
    const risk = prediction?.risk_level || 'UNKNOWN';
    const score = prediction?.health_score ?? '-';

    return (
        <div className="flex flex-col gap-4 p-6">
            <header className="flex flex-col gap-4 rounded-lg border border-slate-800 bg-[#13151f] p-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                    <button type="button" onClick={() => navigate('/')} className="mb-3 border-transparent bg-transparent px-0 py-0 text-xs text-slate-500 hover:bg-transparent hover:text-slate-300">
                        Back to dashboard
                    </button>
                    <h1 className="text-xl font-bold text-slate-100">{transformer.name}</h1>
                    <p className="mt-1 text-xs text-slate-500">
                        {transformer.transformer_id} | {transformer.capacity_kva} kVA | Installed {transformer.installation_year} | {transformer.substation_name}
                    </p>
                </div>

                <div className="text-left lg:text-right">
                    <div className="text-4xl font-black" style={{ color: RISK_COLOR[risk] }}>
                        {score}
                    </div>
                    <div className="text-[11px] uppercase tracking-normal text-slate-500">Health score</div>
                    <span
                        className="mt-2 inline-flex rounded-md border px-3 py-1 text-xs font-bold"
                        style={{
                            borderColor: RISK_COLOR[risk],
                            color: RISK_COLOR[risk],
                            background: `${RISK_COLOR[risk]}22`,
                        }}
                    >
                        {risk}
                    </span>
                </div>
            </header>

            {prediction && (
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <StatCard label="Failure Probability (30d)" value={`${(prediction.failure_probability_30d * 100).toFixed(0)}%`} color={RISK_COLOR[risk]} />
                    <StatCard label="Anomaly Detected" value={prediction.anomaly_detected ? 'YES' : 'NO'} color={prediction.anomaly_detected ? '#dc2626' : '#16a34a'} />
                    <StatCard label="District" value={transformer.district} color="#60a5fa" />
                    <StatCard label="Capacity" value={`${transformer.capacity_kva} kVA`} />
                </div>
            )}

            <nav className="flex gap-2">
                <TabButton active={activeTab === 'overview'} onClick={() => setActiveTab('overview')}>Overview</TabButton>
                <TabButton active={activeTab === 'analytics'} onClick={() => setActiveTab('analytics')}>Analytics</TabButton>
            </nav>

            {activeTab === 'overview' ? (
                <OverviewTab transformer={transformer} prediction={prediction} />
            ) : (
                <TransformerAnalyticsTab transformerId={transformer.transformer_id} />
            )}

            {detail.recent_alerts?.length > 0 && (
                <section className="overflow-hidden rounded-lg border border-slate-800 bg-[#13151f]">
                    <div className="border-b border-slate-800 px-4 py-3 text-sm font-semibold text-slate-100">Recent Alerts</div>
                    {detail.recent_alerts.map((alert) => (
                        <div key={alert.id} className="flex items-center gap-3 border-b border-slate-900 px-4 py-3 last:border-b-0">
                            <div className="h-2 w-2 rounded-full" style={{ background: alert.severity === 'CRITICAL' ? '#dc2626' : '#ca8a04' }} />
                            <div className="flex-1 text-sm text-slate-300">{alert.message}</div>
                            <div className="whitespace-nowrap text-xs text-slate-500">
                                {new Date(alert.triggered_at).toLocaleDateString('en-IN')}
                            </div>
                        </div>
                    ))}
                </section>
            )}
        </div>
    );
}
