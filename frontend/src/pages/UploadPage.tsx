import { useState, useEffect } from "react";
import { IngestionService } from "../api";
import toast from "react-hot-toast";
import {
  UploadCloud,
  File,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
} from "lucide-react";

const StatusIcon = ({ status }: { status: string }) => {
  if (status === "COMPLETED")
    return <CheckCircle size={16} color="var(--accent-success)" />;
  if (status === "PARTIAL")
    return <AlertTriangle size={16} color="var(--accent-warning)" />;
  if (status === "FAILED")
    return <XCircle size={16} color="var(--accent-danger)" />;
  return <Clock size={16} color="var(--text-muted)" />;
};

const UploadPage = () => {
  const [sources, setSources] = useState<any[]>([]);
  const [selectedSource, setSelectedSource] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [batches, setBatches] = useState<any[]>([]);
  const sourceCountLabel = sources.length
    ? `${sources.length} sources connected`
    : "Connecting sources…";

  useEffect(() => {
    IngestionService.getDataSources().then(setSources);
    IngestionService.getBatches()
      .then(setBatches)
      .catch(() => {});
  }, []);

  const handleUpload = async () => {
    if (!file || !selectedSource) {
      toast.error("Please select a data source and a file.");
      return;
    }

    setIsUploading(true);
    setResult(null);
    try {
      const data = await IngestionService.uploadFile(file, selectedSource);
      setResult(data);
      if (data.status === "COMPLETED") {
        toast.success(`Successfully ingested ${data.success_rows} rows`);
      } else if (data.status === "PARTIAL") {
        toast.success(
          `Ingested ${data.success_rows} rows with ${data.error_rows} errors`,
        );
      } else {
        toast.error(`Upload failed. ${data.error_rows} error(s).`);
      }
      // Refresh batch history
      IngestionService.getBatches()
        .then(setBatches)
        .catch(() => {});
    } catch (e: any) {
      toast.error(e.response?.data?.error || "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="animate-fade-in page-narrow">
      <div className="page-header">
        <div>
          <p className="eyebrow">Ingestion</p>
          <h1 className="page-title">Data Ingestion</h1>
          <p className="page-subtitle">
            Upload source exports to normalize and stage records for analyst
            review.
          </p>
        </div>
        <div className="pill">{sourceCountLabel}</div>
      </div>

      <div className="split-grid" style={{ marginBottom: "50px" }}>
        <div className="glass-panel card-padding">
          <div style={{ marginBottom: "24px" }}>
            <label className="form-label">1. Select Data Source</label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="select"
              style={{ width: "100%" }}
            >
              <option value="">-- Select Source --</option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.source_type})
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: "32px" }}>
            <label className="form-label">2. Upload CSV File</label>
            <div className={`dropzone ${file ? "has-file" : ""}`}>
              <input
                type="file"
                accept=".csv"
                onChange={(e) =>
                  setFile(e.target.files ? e.target.files[0] : null)
                }
                style={{ display: "none" }}
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                style={{
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                }}
              >
                {file ? (
                  <>
                    <File
                      size={48}
                      color="var(--accent-primary)"
                      style={{ marginBottom: "16px" }}
                    />
                    <span style={{ fontSize: "18px", fontWeight: 600 }}>
                      {file.name}
                    </span>
                    <span
                      style={{
                        color: "var(--text-secondary)",
                        marginTop: "8px",
                      }}
                    >
                      {(file.size / 1024).toFixed(2)} KB
                    </span>
                  </>
                ) : (
                  <>
                    <UploadCloud
                      size={48}
                      color="var(--text-muted)"
                      style={{ marginBottom: "16px" }}
                    />
                    <span style={{ fontSize: "18px", fontWeight: 600 }}>
                      Click to browse or drag and drop
                    </span>
                    <span
                      style={{
                        color: "var(--text-secondary)",
                        marginTop: "8px",
                      }}
                    >
                      CSV files only. Max 5MB.
                    </span>
                  </>
                )}
              </label>
            </div>

            <div
              style={{
                marginTop: "16px",
                display: "flex",
                gap: "8px",
                flexWrap: "wrap",
                justifyContent: "center",
              }}
            >
              <a
                href="/sample_data/sap_fuel_export.csv"
                download
                className="button"
                style={{
                  fontSize: "12px",
                  padding: "6px 12px",
                  background: "var(--bg-secondary)",
                  color: "var(--text-secondary)",
                }}
              >
                Download SAP Sample
              </a>
              <a
                href="/sample_data/utility_electricity.csv"
                download
                className="button"
                style={{
                  fontSize: "12px",
                  padding: "6px 12px",
                  background: "var(--bg-secondary)",
                  color: "var(--text-secondary)",
                }}
              >
                Download Utility Sample
              </a>
              <a
                href="/sample_data/travel_expenses.csv"
                download
                className="button"
                style={{
                  fontSize: "12px",
                  padding: "6px 12px",
                  background: "var(--bg-secondary)",
                  color: "var(--text-secondary)",
                }}
              >
                Download Travel Sample
              </a>
            </div>
          </div>

          <button
            onClick={handleUpload}
            disabled={isUploading || !file || !selectedSource}
            className="button button-primary"
            style={{ width: "100%", padding: "16px", fontSize: "16px" }}
          >
            {isUploading ? "Processing…" : "Ingest Data"}
          </button>
        </div>

        <div
          className="glass-panel card-padding "
          style={{ marginTop: "50px" }}
        >
          <p className="eyebrow">Readiness</p>
          <h3 className="card-title" style={{ marginTop: "8px" }}>
            Ingestion checklist
          </h3>
          <ul className="checklist">
            <li>
              <CheckCircle size={16} color="var(--accent-success)" /> Validate
              column headers match the source template.
            </li>
            <li>
              <CheckCircle size={16} color="var(--accent-success)" /> Ensure
              activity dates are within the reporting window.
            </li>
            <li>
              <CheckCircle size={16} color="var(--accent-success)" /> Confirm
              units are normalized (kg, kWh, liters).
            </li>
            <li>
              <CheckCircle size={16} color="var(--accent-success)" /> File hash
              dedup prevents duplicate uploads.
            </li>
          </ul>

          <div style={{ marginTop: "20px" }}>
            <p className="eyebrow">What happens next</p>
            <p className="page-subtitle">
              Files are parsed, normalized, and queued for analyst review with
              anomaly detection enabled.
            </p>
          </div>
        </div>
      </div>

      {result && (
        <div
          className="glass-panel animate-slide-in card-padding"
          style={{
            marginBottom: "24px",
            borderLeft: `4px solid ${result.status === "COMPLETED" ? "var(--accent-success)" : result.status === "PARTIAL" ? "var(--accent-warning)" : "var(--accent-danger)"}`,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              marginBottom: "16px",
            }}
          >
            <StatusIcon status={result.status} />
            <h3 style={{ margin: 0 }}>Batch {result.status}</h3>
          </div>
          <div style={{ display: "flex", gap: "24px" }}>
            <div>
              <p style={{ color: "var(--text-secondary)", margin: 0 }}>
                Total Rows
              </p>
              <h4 style={{ margin: "4px 0 0 0", fontSize: "20px" }}>
                {result.total_rows}
              </h4>
            </div>
            <div>
              <p style={{ color: "var(--accent-success)", margin: 0 }}>
                Success
              </p>
              <h4 style={{ margin: "4px 0 0 0", fontSize: "20px" }}>
                {result.success_rows}
              </h4>
            </div>
            <div>
              <p style={{ color: "var(--accent-danger)", margin: 0 }}>Errors</p>
              <h4 style={{ margin: "4px 0 0 0", fontSize: "20px" }}>
                {result.error_rows}
              </h4>
            </div>
          </div>
          {Object.keys(result.error_log).length > 0 && (
            <div
              style={{
                marginTop: "16px",
                padding: "12px",
                background: "rgba(220, 38, 38, 0.08)",
                borderRadius: "8px",
                fontSize: "14px",
                maxHeight: "150px",
                overflow: "auto",
                border: "1px solid rgba(220, 38, 38, 0.2)",
              }}
            >
              {Object.entries(result.error_log).map(([row, msg]: any) => (
                <div key={row} style={{ marginBottom: "4px" }}>
                  <strong>Row {row}:</strong> {msg}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Batch Upload History */}
      {batches.length > 0 && (
        <div className="glass-panel card-padding">
          <div className="card-header">
            <h3 className="card-title">Upload History</h3>
            <span className="chip">{batches.length} batches</span>
          </div>
          <div
            style={{
              overflowX: "auto",
              margin: "16px -24px -24px -24px",
              paddingBottom: "8px",
            }}
          >
            <table className="data-table" style={{ minWidth: "650px" }}>
              <thead>
                <tr>
                  <th style={{ paddingLeft: "24px" }}>File</th>
                  <th>Source</th>
                  <th>Status</th>
                  <th>Rows</th>
                  <th>Errors</th>
                  <th style={{ paddingRight: "24px" }}>Uploaded</th>
                </tr>
              </thead>
              <tbody>
                {batches.slice(0, 10).map((batch: any) => (
                  <tr
                    key={batch.id}
                    className="data-row"
                    style={{ cursor: "default" }}
                  >
                    <td
                      style={{
                        fontWeight: 500,
                        paddingLeft: "24px",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {batch.file_name}
                    </td>
                    <td
                      style={{
                        fontSize: "13px",
                        color: "var(--text-secondary)",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {batch.data_source_name || "—"}
                    </td>
                    <td>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <StatusIcon status={batch.status} />
                        <span style={{ fontSize: "13px" }}>{batch.status}</span>
                      </div>
                    </td>
                    <td>{batch.total_rows}</td>
                    <td
                      style={{
                        color:
                          batch.error_rows > 0
                            ? "var(--accent-danger)"
                            : "var(--text-muted)",
                      }}
                    >
                      {batch.error_rows}
                    </td>
                    <td
                      style={{
                        fontSize: "13px",
                        color: "var(--text-muted)",
                        paddingRight: "24px",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {batch.created_at
                        ? new Date(batch.created_at).toLocaleDateString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
