import React, { useState, useRef } from "react";
import { Upload, X, Film, AlertCircle, CheckCircle2 } from "lucide-react";

export default function UploadModal({ isOpen, onClose, onUploadFile, isUploading }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  if (!isOpen) return null;

  const allowedExts = [".mp4", ".avi", ".mov", ".mkv", ".webm"];

  const validateAndSet = (file) => {
    setError(null);
    if (!file) return;

    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!allowedExts.includes(ext)) {
      setError(`Unsupported file format '${ext}'. Allowed: MP4, AVI, MOV, MKV, WEBM.`);
      return;
    }

    if (file.size > 200 * 1024 * 1024) {
      setError("File size exceeds the 200 MB limit.");
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSet(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedFile) {
      onUploadFile(selectedFile);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-junction-line bg-junction-panel p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-junction-line pb-3 mb-4">
          <div className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-junction-accent/20 text-junction-accent">
              <Upload className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                UPLOAD CCTV FOOTAGE
              </h3>
              <p className="text-xs text-junction-muted">
                Run computer-vision conflict intelligence on traffic video
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-junction-muted hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`flex flex-col items-center justify-center p-8 rounded-xl border-2 border-dashed transition-all cursor-pointer ${
              isDragging
                ? "border-junction-accent bg-junction-accent/10"
                : "border-junction-line hover:border-junction-accent/50 bg-junction-bg/50"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".mp4,.avi,.mov,.mkv,.webm"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  validateAndSet(e.target.files[0]);
                }
              }}
              className="hidden"
            />

            <Film className="w-10 h-10 text-junction-accent mb-2 opacity-70" />
            <p className="text-xs font-semibold text-slate-200 text-center">
              {selectedFile ? selectedFile.name : "Click to browse or drop CCTV video here"}
            </p>
            <p className="text-[10px] text-junction-muted mt-1 font-mono">
              MP4, AVI, MOV, MKV up to 200 MB
            </p>

            {selectedFile && (
              <div className="mt-3 flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>
                  VIDEO SELECTED: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
            )}
          </div>

          {error && (
            <div className="flex items-center space-x-2 text-xs text-red-400 bg-red-500/10 p-2.5 rounded-lg border border-red-500/20 font-mono">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-lg bg-junction-panel2 border border-junction-line text-xs font-medium text-slate-300 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              className="px-4 py-2 rounded-lg bg-junction-accent hover:bg-sky-400 text-junction-bg font-bold text-xs shadow-md transition-all disabled:opacity-50"
            >
              {isUploading ? "Uploading..." : "Start Analysis"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
