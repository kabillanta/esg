import { useState, useEffect } from 'react';
import { RecordsService } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';
import { Activity, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

const COLORS = ['#5fe0c5', '#7ca7ff', '#f2b35d', '#4ed1a3', '#ef6b6b'];

const StatCard = ({ title, value, icon, tone }: any) => (
  <div className={`stat-card stat-${tone}`}>
    <div>
      <p className="stat-title">{title}</p>
      <h3 className="stat-value">{value}</h3>
    </div>
    <div className="stat-icon">{icon}</div>
  </div>
);

const DashboardPage = () => {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    RecordsService.getDashboardStats().then(setStats);
  }, []);

  if (!stats) return <div>Loading dashboard...</div>;

  const scopeData = stats.scope_breakdown.map((s: any) => ({
    name: s.scope.replace('_', ' '),
    value: parseFloat(s.total_co2e)
  }));

  const sourceData = stats.source_breakdown.map((s: any) => ({
    name: s.source_type.replace(/_/g, ' '),
    value: parseFloat(s.total_co2e)
  }));

  const approvedCount = stats.status_breakdown.find((s: any) => s.status === 'APPROVED')?.count || 0;
  const totalRecords = stats.status_breakdown.reduce((sum: number, s: any) => sum + s.count, 0);
  const approvedRate = totalRecords ? Math.round((approvedCount / totalRecords) * 100) : 0;

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1 className="page-title">Enterprise ESG Overview</h1>
          <p className="page-subtitle">A consolidated view of emissions, review workload, and anomalies across all sources.</p>
        </div>
        <div className="pill">FY2026 Q2 · Global snapshot</div>
      </div>
      
      <div className="stat-grid">
        <StatCard 
          title="Total Emissions (kg CO₂e)" 
          value={stats.total_co2e_kg ? parseFloat(stats.total_co2e_kg).toLocaleString(undefined, {maximumFractionDigits: 0}) : 0} 
          icon={<Activity size={24} />} 
          tone="primary" 
        />
        <StatCard 
          title="Pending Review" 
          value={stats.pending_review_count} 
          icon={<Clock size={24} />} 
          tone="warning" 
        />
        <StatCard 
          title="Anomalies Detected" 
          value={stats.anomalies_count} 
          icon={<AlertTriangle size={24} />} 
          tone="danger" 
        />
        <StatCard 
          title="Approved Records" 
          value={approvedCount} 
          icon={<CheckCircle size={24} />} 
          tone="success" 
        />
      </div>

      <div className="glass-panel card-padding insight-card">
        <div className="insight-row">
          <div>
            <p className="eyebrow">Review health</p>
            <h3 className="card-title">Approval readiness</h3>
            <p className="page-subtitle">Progress toward audit-ready records with anomalies surfaced for attention.</p>
          </div>
          <div className="insight-metric">{approvedRate}%</div>
        </div>
        <div className="progress-track">
          <div className="progress-bar" style={{ width: `${approvedRate}%` }}></div>
        </div>
        <div className="insight-footer">
          <span>{stats.pending_review_count} pending review</span>
          <span>{stats.anomalies_count} anomalies flagged</span>
          <span>{totalRecords} total records</span>
        </div>
      </div>

      <div className="chart-grid">
        <div className="glass-panel card-padding">
          <div className="card-header">
            <h3 className="card-title">Emissions by Scope</h3>
            <span className="chip">kg CO₂e</span>
          </div>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scopeData}>
                <XAxis dataKey="name" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.04)'}} contentStyle={{background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '12px', color: 'var(--text-primary)'}} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {scopeData.map((entry: any, index: number) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel card-padding">
          <div className="card-header">
            <h3 className="card-title">Emissions by Source Type</h3>
            <span className="chip">Share</span>
          </div>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={sourceData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({name, percent = 0}) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {sourceData.map((entry: any, index: number) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '12px', color: 'var(--text-primary)'}} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
