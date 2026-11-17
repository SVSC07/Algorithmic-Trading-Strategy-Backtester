import React, { useState, useEffect } from 'react';
import type { Instrument, ImportPricesResponse } from '../types/api';
import {
  listInstruments,
  createInstrument,
  updateInstrument,
  deleteInstrument,
  importPrices,
} from '../api/instruments';
import { ApiError } from '../api/http';
import { CustomSelect } from '../components/CustomSelect';
import {
  Plus,
  Edit2,
  Trash2,
  Upload,
  Check,
  X,
  FileSpreadsheet,
  AlertTriangle,
  Database,
  Calendar,
} from 'lucide-react';

export const AdminInstruments: React.FC = () => {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New Instrument Form state
  const [isAdding, setIsAdding] = useState(false);
  const [newTicker, setNewTicker] = useState('');
  const [newName, setNewName] = useState('');
  const [newAssetClass, setNewAssetClass] = useState('EQUITY');

  // Inline Edit state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTicker, setEditTicker] = useState('');
  const [editName, setEditName] = useState('');
  const [editAssetClass, setEditAssetClass] = useState('');

  // Delete Confirm modal/state
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  // CSV Import state & report
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  const [importReport, setImportReport] = useState<{
    ticker: string;
    report: ImportPricesResponse;
  } | null>(null);

  const fetchInstruments = async () => {
    try {
      setLoading(true);
      const data = await listInstruments();
      setInstruments(data);
    } catch (err) {
      if (err instanceof ApiError) setErrorMsg(err.message);
      else setErrorMsg('Failed to load instruments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInstruments();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setActionLoading(true);

    try {
      const created = await createInstrument(newTicker.trim(), newName.trim(), newAssetClass.trim());
      setInstruments((prev) => [...prev, created]);
      setSuccessMsg(`Instrument ${created.ticker} added successfully.`);
      setIsAdding(false);
      setNewTicker('');
      setNewName('');
    } catch (err) {
      if (err instanceof ApiError) setErrorMsg(err.message);
      else setErrorMsg('Failed to create instrument');
    } finally {
      setActionLoading(false);
    }
  };

  const startEdit = (inst: Instrument) => {
    setEditingId(inst.instrument_id);
    setEditTicker(inst.ticker);
    setEditName(inst.name);
    setEditAssetClass(inst.asset_class);
  };

  const cancelEdit = () => {
    setEditingId(null);
  };

  const handleSaveEdit = async (id: number) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setActionLoading(true);

    try {
      const updated = await updateInstrument(id, editTicker.trim(), editName.trim(), editAssetClass.trim());
      setInstruments((prev) => prev.map((item) => (item.instrument_id === id ? updated : item)));
      setSuccessMsg(`Instrument ${updated.ticker} updated successfully.`);
      setEditingId(null);
    } catch (err) {
      if (err instanceof ApiError) setErrorMsg(err.message);
      else setErrorMsg('Failed to update instrument');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setActionLoading(true);

    try {
      await deleteInstrument(id);
      setInstruments((prev) => prev.filter((item) => item.instrument_id !== id));
      setSuccessMsg(`Instrument deleted successfully.`);
      setConfirmDeleteId(null);
    } catch (err) {
      if (err instanceof ApiError) setErrorMsg(err.message);
      else setErrorMsg('Failed to delete instrument');
    } finally {
      setActionLoading(false);
    }
  };

  const handleFileUpload = async (id: number, ticker: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setErrorMsg(null);
    setSuccessMsg(null);
    setUploadingId(id);

    try {
      const report = await importPrices(id, file);
      setImportReport({ ticker, report });
      setSuccessMsg(`Price series processed for ${ticker}.`);
      fetchInstruments(); // Refresh bar counts and dates
    } catch (err) {
      if (err instanceof ApiError) setErrorMsg(err.message);
      else setErrorMsg('Failed to upload price data');
    } finally {
      setUploadingId(null);
      e.target.value = '';
    }
  };

  if (loading) {
    return <div className="empty-state">Loading instrument administrative registry...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title & Action */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            Instrument Administration
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Manage tradeable universe, edit assets, and import historical EOD bar series (FR-8).
          </p>
        </div>

        <button
          onClick={() => setIsAdding(!isAdding)}
          className="btn btn-primary"
          style={{ padding: '10px 20px' }}
        >
          <Plus size={16} />
          <span>{isAdding ? 'Cancel' : 'Add Instrument'}</span>
        </button>
      </div>

      {errorMsg && (
        <div className="alert-error" role="alert">
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="alert-success" role="status">
          {successMsg}
        </div>
      )}

      {/* Add Instrument Drawer / Form */}
      {isAdding && (
        <div className="card animate-fade-in" style={{ border: '2px solid var(--accent-lime)' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>
            Register New Market Instrument
          </h2>
          <form onSubmit={handleCreate}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="new-ticker-input">
                  Ticker Symbol
                </label>
                <input
                  id="new-ticker-input"
                  type="text"
                  className="form-input"
                  placeholder="e.g. INFY"
                  value={newTicker}
                  onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="new-name-input">
                  Instrument Name
                </label>
                <input
                  id="new-name-input"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Infosys Ltd"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="new-asset-class-input">
                  Asset Class
                </label>
                <CustomSelect
                  id="new-asset-class-input"
                  value={newAssetClass}
                  onChange={(val) => setNewAssetClass(String(val))}
                  options={[
                    { value: 'EQUITY', label: 'EQUITY' },
                    { value: 'COMMODITY', label: 'COMMODITY' },
                    { value: 'FOREX', label: 'FOREX' },
                    { value: 'CRYPTO', label: 'CRYPTO' },
                  ]}
                />
              </div>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setIsAdding(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={actionLoading}
              >
                {actionLoading ? 'Saving...' : 'Add to Universe'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* CSV Import Report Modal / Card */}
      {importReport && (
        <div className="card" style={{ border: '2px solid var(--accent-dark)', background: '#F9FAFB' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileSpreadsheet size={20} color="var(--accent-dark)" />
              <h2 style={{ fontSize: '17px', fontWeight: 700 }}>
                Price Import Report: {importReport.ticker}
              </h2>
            </div>
            <button
              onClick={() => setImportReport(null)}
              className="btn btn-secondary"
              style={{ padding: '4px 10px', fontSize: '12px' }}
            >
              <X size={14} />
              <span>Dismiss</span>
            </button>
          </div>

          <div style={{ display: 'flex', gap: '20px', marginBottom: '16px' }}>
            <div className="badge badge-gain" style={{ fontSize: '13px', padding: '6px 14px' }}>
              Imported: {importReport.report.imported} bars
            </div>
            <div className="badge badge-neutral" style={{ fontSize: '13px', padding: '6px 14px' }}>
              Skipped: {importReport.report.skipped} bars
            </div>
          </div>

          {importReport.report.errors.length > 0 ? (
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--loss)', marginBottom: '8px' }}>
                First Errors Encountered:
              </div>
              <ul style={{ paddingLeft: '20px', fontSize: '13px', color: 'var(--loss-text)' }}>
                {importReport.report.errors.slice(0, 5).map((err, idx) => (
                  <li key={`err-${idx}`}>
                    Row {err.row}: {err.reason}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div style={{ fontSize: '13px', color: 'var(--gain-text)', fontWeight: 500 }}>
              ✓ All records parsed and imported without validation errors.
            </div>
          )}
        </div>
      )}

      {/* Instrument Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={18} color="var(--text-muted)" />
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Active Instrument Universe</h2>
          </div>
          <span className="badge badge-neutral">
            {instruments.length} registered
          </span>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Name</th>
                <th>Asset Class</th>
                <th>Coverage (Start → End)</th>
                <th className="text-right">Bars</th>
                <th>Import CSV</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {instruments.map((inst) => {
                const isEditing = editingId === inst.instrument_id;
                return (
                  <tr key={inst.instrument_id}>
                    <td>
                      {isEditing ? (
                        <input
                          type="text"
                          className="form-input"
                          style={{ padding: '6px 10px', fontSize: '13px' }}
                          value={editTicker}
                          onChange={(e) => setEditTicker(e.target.value.toUpperCase())}
                        />
                      ) : (
                        <span className="badge badge-dark" style={{ fontWeight: 700 }}>
                          {inst.ticker}
                        </span>
                      )}
                    </td>

                    <td>
                      {isEditing ? (
                        <input
                          type="text"
                          className="form-input"
                          style={{ padding: '6px 10px', fontSize: '13px' }}
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                        />
                      ) : (
                        <span style={{ fontWeight: 500 }}>{inst.name}</span>
                      )}
                    </td>

                    <td>
                      {isEditing ? (
                        <CustomSelect
                          value={editAssetClass}
                          onChange={(val) => setEditAssetClass(String(val))}
                          size="small"
                          options={[
                            { value: 'EQUITY', label: 'EQUITY' },
                            { value: 'COMMODITY', label: 'COMMODITY' },
                            { value: 'FOREX', label: 'FOREX' },
                            { value: 'CRYPTO', label: 'CRYPTO' },
                          ]}
                          style={{ minWidth: '130px' }}
                        />
                      ) : (
                        <span className="badge badge-neutral">{inst.asset_class}</span>
                      )}
                    </td>

                    <td style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                      {inst.data_start && inst.data_end ? (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Calendar size={13} />
                          {inst.data_start} → {inst.data_end}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)' }}>No data</span>
                      )}
                    </td>

                    <td className="text-right tabular-nums" style={{ fontWeight: 600 }}>
                      {inst.bar_count}
                    </td>

                    <td>
                      <label
                        className="btn btn-secondary"
                        style={{
                          padding: '5px 12px',
                          fontSize: '12px',
                          cursor: uploadingId === inst.instrument_id ? 'wait' : 'pointer',
                        }}
                      >
                        <Upload size={13} />
                        <span>{uploadingId === inst.instrument_id ? 'Uploading...' : 'Upload CSV'}</span>
                        <input
                          type="file"
                          accept=".csv"
                          style={{ display: 'none' }}
                          disabled={uploadingId === inst.instrument_id}
                          onChange={(e) => handleFileUpload(inst.instrument_id, inst.ticker, e)}
                        />
                      </label>
                    </td>

                    <td className="text-right">
                      {isEditing ? (
                        <div style={{ display: 'inline-flex', gap: '6px' }}>
                          <button
                            onClick={() => handleSaveEdit(inst.instrument_id)}
                            className="btn btn-lime"
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            title="Save changes"
                          >
                            <Check size={14} />
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="btn btn-secondary"
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            title="Cancel editing"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: 'inline-flex', gap: '6px' }}>
                          <button
                            onClick={() => startEdit(inst)}
                            className="btn btn-secondary"
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            title="Edit instrument"
                          >
                            <Edit2 size={13} />
                          </button>
                          <button
                            onClick={() => setConfirmDeleteId(inst.instrument_id)}
                            className="btn btn-danger"
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            title="Delete instrument"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {confirmDeleteId !== null && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.45)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            className="card animate-fade-in"
            style={{ width: '90%', maxWidth: '420px', padding: '28px', background: '#FFFFFF' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
              <div
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '50%',
                  background: 'var(--loss-bg)',
                  color: 'var(--loss)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <AlertTriangle size={20} />
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Confirm Removal</h3>
            </div>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '20px' }}>
              Are you sure you want to remove this instrument? If backtest runs reference it, deletion will be rejected (409 Conflict).
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => setConfirmDeleteId(null)}
                className="btn btn-secondary"
                disabled={actionLoading}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDeleteId)}
                className="btn btn-danger"
                disabled={actionLoading}
              >
                {actionLoading ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
