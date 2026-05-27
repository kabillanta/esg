import { useState, useEffect } from 'react';
import { AuthService, RecordsService } from '../api';
import toast from 'react-hot-toast';
import { Filter, Search, X, CheckCircle, AlertTriangle, ChevronRight, Lock, XCircle } from 'lucide-react';
import { Navigate } from 'react-router-dom';

const StatusBadge = ({ status }: { status: string }) => {
  const statusClass = `status-badge status-${status.toLowerCase()}`;
  return <span className={statusClass}>{status}</span>;
};

const ScopeBadge = ({ scope }: { scope: string }) => {
  const label = scope.replace('_', ' ');
  return <span className="chip" style={{ fontSize: '11px', padding: '3px 8px' }}>{label}</span>;
};

const RecordsPage = () => {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState<any>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [scopeFilter, setScopeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isFlagging, setIsFlagging] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [flagReason, setFlagReason] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const currentUser = AuthService.getCurrentUser();
  if (!currentUser || currentUser.role !== 'ADMIN') {
    return <Navigate to="/" replace />;
  }
  
  const fetchRecords = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      if (scopeFilter) params.scope = scopeFilter;
      const data = await RecordsService.getRecords(params);
      setRecords(data.results || data);
    } catch (e) {
      toast.error('Failed to load records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [statusFilter, scopeFilter]);

  const handleApprove = async (id: string) => {
    try {
      const updated = await RecordsService.approveRecord(id);
      toast.success('Record approved and locked for audit');
      setRecords(records.map(r => r.id === id ? updated : r));
      setSelectedRecord(updated);
      setIsFlagging(false);
      setIsRejecting(false);
      setFlagReason('');
      setRejectReason('');
    } catch (e: any) {
      toast.error(e.response?.data?.error || 'Failed to approve');
    }
  };

  const handleFlag = async (id: string, reason: string) => {
    if (!reason) {
      toast.error('Please provide a reason for flagging.');
      return;
    }
    try {
      const updated = await RecordsService.flagRecord(id, reason);
      toast.success('Record flagged');
      setRecords(records.map(r => r.id === id ? updated : r));
      setSelectedRecord(updated);
      setIsFlagging(false);
      setFlagReason('');
    } catch (e: any) {
      toast.error(e.response?.data?.error || 'Failed to flag');
    }
  };

  const handleReject = async (id: string, reason: string) => {
    if (!reason) {
      toast.error('Please provide a reason for rejection.');
      return;
    }
    try {
      const updated = await RecordsService.rejectRecord(id, reason);
      toast.success('Record rejected');
      setRecords(records.map(r => r.id === id ? updated : r));
      setSelectedRecord(updated);
      setIsRejecting(false);
      setRejectReason('');
    } catch (e: any) {
      toast.error(e.response?.data?.error || 'Failed to reject');
    }
  };

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredRecords = records.filter(record => {
    if (!normalizedQuery) return true;
    const haystack = [
      record.category,
      record.description,
      record.activity_date,
      record.unit_normalized,
      record.source_type,
      record.scope,
      record.id
    ].filter(Boolean).join(' ').toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  const isLocked = selectedRecord?.status === 'APPROVED';

  return (
    <div className="records-shell">
      
      {/* Main Table Area */}
      <div className="records-main">
        <div className="records-header">
          <div>
            <p className="eyebrow">Review</p>
            <h1 className="page-title" style={{ margin: 0 }}>Record review queue</h1>
            <p className="page-subtitle" style={{ marginBottom: 0 }}>
              Approve or flag records before they are locked for audit.
            </p>
          </div>
          
          <div className="filters">
            <div className="input-with-icon">
              <Filter size={16} />
              <select 
                value={statusFilter} 
                onChange={e => setStatusFilter(e.target.value)}
                className="select"
                style={{ width: '160px' }}
              >
                <option value="">All Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="APPROVED">Approved</option>
                <option value="FLAGGED">Flagged</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>

            <div className="input-with-icon">
              <Filter size={16} />
              <select
                value={scopeFilter}
                onChange={e => setScopeFilter(e.target.value)}
                className="select"
                style={{ width: '150px' }}
              >
                <option value="">All Scopes</option>
                <option value="SCOPE_1">Scope 1</option>
                <option value="SCOPE_2">Scope 2</option>
                <option value="SCOPE_3">Scope 3</option>
              </select>
            </div>
            
            <div className="input-with-icon">
              <Search size={16} />
              <input 
                type="text" 
                placeholder="Search records…" 
                className="input"
                style={{ width: '220px' }}
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="table-meta">
          <span>{loading ? 'Loading records…' : `${filteredRecords.length} records ready for review`}</span>
        </div>

        <div className="glass-panel table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Scope</th>
                <th>Source</th>
                <th>Category</th>
                <th>Qty (Norm)</th>
                <th>Emissions</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} style={{ padding: '24px', textAlign: 'center' }}>Loading...</td></tr>
              ) : filteredRecords.length === 0 ? (
                <tr><td colSpan={8} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No records match this view</td></tr>
              ) : (
                filteredRecords.map(record => (
                  <tr 
                    key={record.id} 
                    onClick={() => {
                      setSelectedRecord(record);
                      setIsFlagging(false);
                      setIsRejecting(false);
                      setFlagReason('');
                      setRejectReason('');
                    }}
                    className={`data-row ${selectedRecord?.id === record.id ? 'selected' : ''}`}
                  >
                    <td>{record.activity_date}</td>
                    <td><ScopeBadge scope={record.scope} /></td>
                    <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{record.source_type.replace(/_/g, ' ')}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {record.is_anomaly && <AlertTriangle size={14} color="var(--accent-warning)" />}
                        {record.category}
                      </div>
                    </td>
                    <td>{parseFloat(record.quantity_normalized).toLocaleString()} {record.unit_normalized}</td>
                    <td style={{ fontWeight: 600 }}>{record.co2e_kg ? parseFloat(record.co2e_kg).toLocaleString() : '—'} kg</td>
                    <td><StatusBadge status={record.status} /></td>
                    <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>
                      {record.status === 'APPROVED' ? <Lock size={16} /> : <ChevronRight size={18} />}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Side Panel */}
      {selectedRecord && (
        <div className="side-panel animate-slide-in">
          <div className="panel-header">
            <h2 style={{ fontSize: '18px', margin: 0 }}>Record Details</h2>
            <button onClick={() => {
              setSelectedRecord(null);
              setIsFlagging(false);
              setIsRejecting(false);
              setFlagReason('');
              setRejectReason('');
            }} className="icon-button">
              <X size={20} />
            </button>
          </div>
          
          <div className="panel-body">
            
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <StatusBadge status={selectedRecord.status} />
                {isLocked && <Lock size={14} color="var(--accent-primary)" />}
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>ID: {selectedRecord.id.substring(0,8)}...</span>
            </div>

            {isLocked && (
              <div className="alert" style={{ marginBottom: '24px', background: 'rgba(47, 143, 124, 0.08)', borderColor: 'rgba(47, 143, 124, 0.2)' }}>
                <Lock color="var(--accent-primary)" size={18} style={{ flexShrink: 0 }} />
                <div>
                  <h4 style={{ margin: '0 0 4px 0', color: 'var(--accent-primary)', fontSize: '13px' }}>Locked for audit</h4>
                  <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Approved by {selectedRecord.reviewed_by_name || 'reviewer'} on {selectedRecord.reviewed_at ? new Date(selectedRecord.reviewed_at).toLocaleDateString() : '—'}
                  </p>
                </div>
              </div>
            )}

            {selectedRecord.is_anomaly && (
              <div className="alert" style={{ marginBottom: '24px' }}>
                <AlertTriangle color="#f59e0b" size={20} style={{ flexShrink: 0 }} />
                <div>
                  <h4 style={{ margin: '0 0 4px 0', color: '#f59e0b', fontSize: '14px' }}>Anomaly Detected</h4>
                  <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>{selectedRecord.anomaly_reason}</p>
                </div>
              </div>
            )}

            <div style={{ marginBottom: '32px' }}>
              <h3 className="section-title">Provenance</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Scope</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{selectedRecord.scope.replace('_', ' ')}</p>
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Source Type</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{selectedRecord.source_type.replace(/_/g, ' ')}</p>
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Batch</p>
                  <p style={{ margin: 0, fontWeight: 500, fontSize: '13px' }}>{selectedRecord.upload_batch_name || '—'}</p>
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Source Row #</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{selectedRecord.source_row_number}</p>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '32px' }}>
              <h3 className="section-title">Normalized Data</h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Category</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{selectedRecord.category}</p>
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Activity Date</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{selectedRecord.activity_date}</p>
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Original Qty</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{parseFloat(selectedRecord.quantity_original).toLocaleString()} {selectedRecord.unit_original}</p>
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Normalized Qty</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{parseFloat(selectedRecord.quantity_normalized).toLocaleString()} {selectedRecord.unit_normalized}</p>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Emissions CO₂e</p>
                  <p style={{ margin: 0, fontWeight: 600, color: 'var(--accent-primary)', fontSize: '18px' }}>{selectedRecord.co2e_kg ? `${parseFloat(selectedRecord.co2e_kg).toLocaleString()} kg` : 'No emission factor match'}</p>
                </div>
              </div>
              <div style={{ marginTop: '16px' }}>
                <p style={{ color: 'var(--text-secondary)', fontSize: '12px', margin: '0 0 4px 0' }}>Description</p>
                <p style={{ margin: 0, fontSize: '14px' }}>{selectedRecord.description || '—'}</p>
              </div>
            </div>

            <div style={{ marginBottom: '32px' }}>
              <h3 className="section-title">Raw Source Data (JSON)</h3>
              <div className="code-block">
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(selectedRecord.raw_data, null, 2)}
                </pre>
              </div>
            </div>

            {selectedRecord.status === 'FLAGGED' && selectedRecord.flag_reason && (
              <div style={{ marginBottom: '32px' }}>
                <h3 className="section-title" style={{ marginBottom: '8px' }}>Flag Reason</h3>
                <p style={{ margin: 0, fontSize: '14px', color: 'var(--accent-danger)' }}>{selectedRecord.flag_reason}</p>
              </div>
            )}

            {selectedRecord.status === 'REJECTED' && selectedRecord.flag_reason && (
              <div style={{ marginBottom: '32px' }}>
                <h3 className="section-title" style={{ marginBottom: '8px' }}>Rejection Reason</h3>
                <p style={{ margin: 0, fontSize: '14px', color: 'var(--accent-danger)' }}>{selectedRecord.flag_reason}</p>
              </div>
            )}

            {isFlagging && (
              <div className="flag-panel">
                <label className="form-label">Reason for flagging</label>
                <textarea
                  className="textarea"
                  placeholder="Describe the anomaly or policy concern…"
                  value={flagReason}
                  onChange={e => setFlagReason(e.target.value)}
                />
                <div className="flag-actions">
                  <button
                    className="button button-danger"
                    onClick={() => handleFlag(selectedRecord.id, flagReason)}
                  >
                    Submit flag
                  </button>
                  <button
                    className="button button-ghost"
                    onClick={() => {
                      setIsFlagging(false);
                      setFlagReason('');
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {isRejecting && (
              <div className="flag-panel" style={{ background: 'rgba(138, 131, 120, 0.08)', borderColor: 'rgba(138, 131, 120, 0.24)' }}>
                <label className="form-label">Reason for rejection</label>
                <textarea
                  className="textarea"
                  placeholder="Explain why this record is being rejected…"
                  value={rejectReason}
                  onChange={e => setRejectReason(e.target.value)}
                />
                <div className="flag-actions">
                  <button
                    className="button button-danger"
                    onClick={() => handleReject(selectedRecord.id, rejectReason)}
                  >
                    Confirm reject
                  </button>
                  <button
                    className="button button-ghost"
                    onClick={() => {
                      setIsRejecting(false);
                      setRejectReason('');
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
            
          </div>
          
          {!isLocked && (
            <div className="panel-footer">
              <button 
                onClick={() => handleApprove(selectedRecord.id)}
                disabled={selectedRecord.status === 'APPROVED'}
                className="button button-primary"
                style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
              >
                <CheckCircle size={18} /> Approve
              </button>
              <button 
                onClick={() => { setIsFlagging(true); setIsRejecting(false); }}
                disabled={selectedRecord.status === 'FLAGGED'}
                className="button button-secondary"
                style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', opacity: selectedRecord.status === 'FLAGGED' ? 0.6 : 1 }}
              >
                <AlertTriangle size={18} color="var(--accent-warning)" /> Flag
              </button>
              <button 
                onClick={() => { setIsRejecting(true); setIsFlagging(false); }}
                disabled={selectedRecord.status === 'REJECTED'}
                className="button button-secondary"
                style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', opacity: selectedRecord.status === 'REJECTED' ? 0.6 : 1 }}
              >
                <XCircle size={18} color="var(--accent-danger)" /> Reject
              </button>
            </div>
          )}
        </div>
      )}
      
    </div>
  );
};

export default RecordsPage;
