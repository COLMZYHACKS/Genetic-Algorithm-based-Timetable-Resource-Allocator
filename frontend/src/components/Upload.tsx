import { useState } from "react";
import API from "../services/api";

interface Props {
  setPath: (path: string) => void;
}

export default function Upload({ setPath }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string>("");

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first");
      return;
    }

    // Validate file type
    const validExtensions = [".csv", ".xlsx", ".xls"];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
    
    if (!hasValidExtension) {
      alert("Please upload a CSV or Excel file (.csv, .xlsx, .xls)");
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await API.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });

      console.log("UPLOAD RESPONSE:", res.data);

      if (res.data.path) {
        setPath(res.data.path);
        setUploadedFileName(file.name);
        alert("Upload successful!");
        setFile(null);
      } else {
        alert("Upload failed: No file path returned");
      }
    } catch (err) {
      console.error("UPLOAD ERROR:", err);
      const errorMessage = (err as any).response?.data?.error || (err as any).message || "Unknown error";
      alert("Upload failed: " + errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="upload-container">
      <div className="upload-surface" onDrop={handleDrop} onDragOver={handleDragOver} onClick={() => document.getElementById('file-input')?.click()} role="button" tabIndex={0}>
        <input
          id="file-input"
          type="file"
          accept=".csv,.xlsx,.xls"
          className="upload-input"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          disabled={isUploading}
          style={{ display: 'none' }}
        />

        <div className="upload-surface-inner">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path d="M12 3v12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M8 7l4-4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <rect x="3" y="13" width="18" height="6" rx="2" stroke="currentColor" strokeWidth="1.5" />
          </svg>
          <div>
            <div className="upload-title">Drag & drop CSV or click to browse</div>
            <div className="upload-sub">Accepted: .csv, .xlsx, .xls</div>
          </div>
        </div>
      </div>

      {file && <p className="upload-selected">✓ {file.name} — Ready to upload</p>}
      {uploadedFileName && <p className="upload-success">✓ Uploaded: {uploadedFileName}</p>}

      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <button
          className="upload-button upload-button-primary"
          onClick={handleUpload}
          disabled={isUploading || !file}
        >
          {isUploading ? (
            <>
              <svg className="loading-spinner" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" strokeDasharray="31.416" strokeDashoffset="31.416">
                  <animate attributeName="stroke-dashoffset" dur="1s" values="31.416;0" repeatCount="indefinite"/>
                </circle>
              </svg>
              Uploading...
            </>
          ) : (
            "Upload"
          )}
        </button>
        <button className="upload-button upload-button-secondary" onClick={() => setFile(null)} disabled={isUploading || !file}>
          Remove
        </button>
      </div>
    </div>
  );
}