import { useState } from "react";
import API from "../services/api";
import Upload from "../components/Upload";
import TimetableGrid from "../components/TimetableGrid";
import ExportButton from "../components/ExportButton";

export default function Dashboard() {
  const [path, setPath] = useState<string>("");
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [useDatabase, setUseDatabase] = useState(false);
  const [timetableType, setTimetableType] = useState<"course" | "exam">("course");
  const [fitnessScore, setFitnessScore] = useState<number | null>(null);

  const generate = async () => {
    if (!useDatabase && (!path || path.trim() === "")) {
      alert("Please upload a file first or switch to database mode");
      return;
    }

    setLoading(true);
    setProgress(10);

    // Simulate progress increments while waiting for response
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 90) return prev + Math.random() * 15;
        return prev;
      });
    }, 300);

    try {
      const res = await API.post("/timetable/generate", {
        path: useDatabase ? null : path,
        use_database: useDatabase,
        type: timetableType
      });

      setProgress(95);

      let responseData = res.data;
      if (typeof res.data === 'string') {
        try {
          responseData = JSON.parse(res.data);
        } catch (parseError) {
          console.error("Failed to parse server response:", parseError);
          alert("Failed to parse server response. Please check the console for details.");
          return;
        }
      }

      if (responseData.error) {
        alert("Generation failed: " + responseData.error);
        return;
      }

      if (responseData.timetable) {
        setData(responseData.timetable);
        setFitnessScore(responseData.fitness ?? responseData.score ?? null);
        setProgress(100);
      } else {
        alert("Generation failed: No timetable data received");
      }
    } catch (err) {
      console.error("Generation error:", err);
      alert("Generation failed: " + ((err as any).response?.data?.error || (err as any).message));
    } finally {
      clearInterval(progressInterval);
      setTimeout(() => {
        setLoading(false);
        setProgress(0);
      }, 500);
    }
  };

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Generate optimized course and examination timetables using your university scheduling data.</p>
        </div>
        <div className="page-meta">
          <p className="last-updated">Last updated: Today</p>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="upload-section">
          <div className="section-header">
            <h2>Data Source</h2>
            <p>Choose how you would like to provide your university scheduling data.</p>
          </div>

          <div className="data-source-row">
            <div
              className={`data-source-card select-indicator ${useDatabase ? 'selected' : ''}`}
              onClick={() => setUseDatabase(true)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setUseDatabase(true); }}
              role="button"
              tabIndex={0}
              aria-pressed={useDatabase}
            >
              <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                <div className="icon-circle" aria-hidden>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="4" width="18" height="6" rx="1" fill="none" stroke="currentColor" strokeWidth="1.4" />
                    <rect x="3" y="12" width="18" height="8" rx="1" fill="none" stroke="currentColor" strokeWidth="1.4" />
                  </svg>
                </div>
                <div>
                  <div className="data-source-title">Use Database</div>
                  <div className="data-source-desc">Load existing university scheduling data from the system.</div>
                </div>
              </div>
            </div>

            <div
              className={`data-source-card select-indicator ${!useDatabase ? 'selected' : ''}`}
              onClick={() => setUseDatabase(false)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setUseDatabase(false); }}
              role="button"
              tabIndex={0}
              aria-pressed={!useDatabase}
            >
              <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                <div className="icon-circle" aria-hidden>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M12 3v9" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
                    <rect x="3" y="14" width="18" height="6" rx="1" fill="none" stroke="currentColor" strokeWidth="1.4" />
                  </svg>
                </div>
                <div>
                  <div className="data-source-title">Upload CSV</div>
                  <div className="data-source-desc">Upload course, lecturer and student data using a CSV file.</div>
                </div>
              </div>
              <div className="upload-area">
                {!useDatabase && (
                  <Upload setPath={setPath} />
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="generate-section">
          <div className="section-header">
            <h2>Timetable Type</h2>
            <p>Select the type of timetable you want to generate.</p>
          </div>
          <div className="generate-card">
            <div className="timetable-type-cards">
              <label className={`option-card ${timetableType === 'course' ? 'selected' : ''}`}>
                <input type="radio" name="ttype" value="course" checked={timetableType === 'course'} onChange={(e) => setTimetableType(e.target.value as "course" | "exam")} />
                <div className="option-content">
                  <div className="option-title">Course Timetable</div>
                  <div className="option-desc">Regular academic schedule</div>
                </div>
              </label>

              <label className={`option-card ${timetableType === 'exam' ? 'selected' : ''}`}>
                <input type="radio" name="ttype" value="exam" checked={timetableType === 'exam'} onChange={(e) => setTimetableType(e.target.value as "course" | "exam")} />
                <div className="option-content">
                  <div className="option-title">Exam Timetable</div>
                  <div className="option-desc">Examination scheduling</div>
                </div>
              </label>
            </div>

            <div className="generate-actions">
              <button
                onClick={generate}
                disabled={loading || (!useDatabase && !path)}
                className={`generate-btn ${loading ? 'loading' : ''}`}
                aria-live="polite"
              >
                {loading ? (
                  <>
                    <svg className="loading-spinner" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" strokeDasharray="31.416" strokeDashoffset="31.416">
                        <animate attributeName="stroke-dashoffset" dur="1s" values="31.416;0" repeatCount="indefinite"/>
                      </circle>
                    </svg>
                    Generating... ({progress}%)
                  </>
                ) : (
                  <>
                    <span aria-hidden style={{ fontSize: 18, marginRight: 8 }}>✨</span>
                    Generate Timetable
                  </>
                )}
              </button>
              {loading && (
                <div className="progress-bar-container">
                  <div className="progress-bar" style={{ width: `${progress}%` }}></div>
                </div>
              )}
            </div>
            {(!useDatabase && !path) && (
              <div className="generate-hint">⚠ Please upload a file or select Use Database before generating.</div>
            )}
          </div>
        </div>

        {/* Empty state when no timetable generated */}
        {(!loading && data.length === 0) && (
          <div className="timetable-empty-state">
            <strong>No timetable yet</strong>
            <p>Upload or load your university data, select a timetable type, and click Generate to create an optimized schedule.</p>
          </div>
        )}

        {data.length > 0 && (
          <div className="results-section">
            <div className="section-header">
              <h2>Generated Timetable</h2>
              <p>Your optimized timetable is ready. You can view it below or export to Excel.</p>
            </div>
            <div className="results-card">
              <div className="results-actions">
                <ExportButton data={data} timetableType={timetableType} />
                <div className="results-stats">
                  <span className="stat">
                    <strong>{data.length}</strong> scheduled classes
                  </span>
                  {fitnessScore !== null && (
                    <span className="stat">
                      <strong>{fitnessScore.toFixed(2)}%</strong> quality score
                    </span>
                  )}
                </div>
              </div>
              <div className="timetable-container">
                <TimetableGrid data={data} timetableType={timetableType} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}