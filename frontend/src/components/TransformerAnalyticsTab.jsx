import { useEffect, useMemo, useState } from 'react';
import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import { getReadings } from '../api/client';

const numberOrNull = (value) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
};

const formatTime = (value) =>
    new Intl.DateTimeFormat('en-IN', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    }).format(new Date(value));

function AnalyticsSkeleton() {
    return (
        <div className="rounded-lg border border-slate-800 bg-[#13151f] p-4">
            <div className="mb-5 flex items-center justify-between">
                <div className="h-4 w-48 animate-pulse rounded bg-slate-800" />
                <div className="h-7 w-24 animate-pulse rounded-md bg-slate-800" />
            </div>
            <div className="h-[320px] animate-pulse rounded-md bg-slate-900/80" />
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div className="h-16 animate-pulse rounded-md bg-slate-900/80" />
                <div className="h-16 animate-pulse rounded-md bg-slate-900/80" />
                <div className="h-16 animate-pulse rounded-md bg-slate-900/80" />
            </div>
        </div>
    );
}

function MetricTile({ label, value, tone = 'text-slate-100' }) {
    return (
        <div className="rounded-lg border border-slate-800 bg-[#0f1117] p-3">
            <div className="text-[11px] font-medium uppercase tracking-normal text-slate-500">{label}</div>
            <div className={`mt-1 text-lg font-bold ${tone}`}>{value}</div>
        </div>
    );
}

export default function TransformerAnalyticsTab({ transformerId }) {
    const [readings, setReadings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        let active = true;

        getReadings(transformerId, 30)
            .then((response) => {
                if (!active) return;

                setError('');
                setReadings(response.data.map((row) => ({
                    recordedAt: row.recorded_at,
                    label: formatTime(row.recorded_at),
                    oilTemperature: numberOrNull(row.oil_temperature_c),
                    thd: numberOrNull(row.harmonic_distortion),
                })));
            })
            .catch((err) => {
                if (!active) return;
                setReadings([]);
                setError(err.response?.status === 404 ? 'No readings available for the selected period.' : 'Unable to load analytics data.');
            })
            .finally(() => {
                if (active) setLoading(false);
            });

        return () => {
            active = false;
        };
    }, [transformerId]);

    const stats = useMemo(() => {
        const oils = readings.map((r) => r.oilTemperature).filter((v) => v != null);
        const thds = readings.map((r) => r.thd).filter((v) => v != null);
        const avg = (items) => (items.length ? items.reduce((sum, item) => sum + item, 0) / items.length : null);

        return {
            maxOil: oils.length ? Math.max(...oils) : null,
            avgThd: avg(thds),
            samples: readings.length,
        };
    }, [readings]);

    if (loading) return <AnalyticsSkeleton />;

    return (
        <section className="rounded-lg border border-slate-800 bg-[#13151f] p-4">
            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-sm font-semibold text-slate-100">Transformer Analytics</h2>
                    <p className="mt-1 text-xs text-slate-500">30-day oil temperature and harmonic distortion trends</p>
                </div>
                <div className="rounded-md border border-rose-900/70 bg-rose-950/30 px-3 py-2 text-xs font-semibold text-rose-300">
                    Critical oil threshold: 85°C
                </div>
            </div>

            {error ? (
                <div className="flex h-72 items-center justify-center rounded-lg border border-dashed border-slate-800 bg-[#0f1117] text-sm text-slate-500">
                    {error}
                </div>
            ) : (
                <>
                    <div className="h-[340px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={readings} margin={{ top: 12, right: 18, left: 0, bottom: 8 }}>
                                <CartesianGrid stroke="#1e2535" strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="label"
                                    minTickGap={28}
                                    tick={{ fill: '#64748b', fontSize: 11 }}
                                    tickLine={false}
                                />
                                <YAxis
                                    yAxisId="temperature"
                                    domain={[0, 'dataMax + 10']}
                                    tick={{ fill: '#64748b', fontSize: 11 }}
                                    tickLine={false}
                                    label={{ value: 'Oil Temperature (°C)', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
                                />
                                <YAxis
                                    yAxisId="thd"
                                    orientation="right"
                                    domain={[0, 'dataMax + 2']}
                                    tick={{ fill: '#64748b', fontSize: 11 }}
                                    tickLine={false}
                                    label={{ value: 'THD (%)', angle: 90, position: 'insideRight', fill: '#94a3b8', fontSize: 11 }}
                                />
                                <Tooltip
                                    labelClassName="text-slate-300"
                                    contentStyle={{
                                        background: '#0f1117',
                                        border: '1px solid #334155',
                                        borderRadius: 8,
                                        color: '#e2e8f0',
                                        fontSize: 12,
                                    }}
                                />
                                <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: 12 }} />
                                <ReferenceLine
                                    yAxisId="temperature"
                                    y={85}
                                    stroke="#ef4444"
                                    strokeDasharray="6 4"
                                    label={{ value: '85°C critical', fill: '#fca5a5', fontSize: 11, position: 'insideTopRight' }}
                                />
                                <Line
                                    yAxisId="temperature"
                                    name="Oil Temperature Trend (°C)"
                                    type="monotone"
                                    dataKey="oilTemperature"
                                    stroke="#f97316"
                                    strokeWidth={2.5}
                                    dot={false}
                                    activeDot={{ r: 4 }}
                                    connectNulls
                                />
                                <Line
                                    yAxisId="thd"
                                    name="Total Harmonic Distortion (THD %)"
                                    type="monotone"
                                    dataKey="thd"
                                    stroke="#38bdf8"
                                    strokeWidth={2.5}
                                    dot={false}
                                    activeDot={{ r: 4 }}
                                    connectNulls
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                        <MetricTile
                            label="Peak oil temperature"
                            value={stats.maxOil == null ? 'No data' : `${stats.maxOil.toFixed(1)}°C`}
                            tone={stats.maxOil >= 85 ? 'text-rose-400' : 'text-emerald-400'}
                        />
                        <MetricTile
                            label="Average THD"
                            value={stats.avgThd == null ? 'No data' : `${stats.avgThd.toFixed(2)}%`}
                            tone="text-sky-300"
                        />
                        <MetricTile label="Samples plotted" value={stats.samples.toLocaleString('en-IN')} />
                    </div>
                </>
            )}
        </section>
    );
}
