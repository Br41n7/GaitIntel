import { useState } from "react";

export default function VideoUpload({
  onUpload,
}: {
  onUpload: (file: File) => Promise<void>;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await onUpload(file);
    } catch (err) {
      setError(String(err));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center">
      <label className="cursor-pointer text-sm font-medium text-slate-700">
        {uploading ? "Uploading…" : "Choose a walking video (.mp4, .mov, .avi, .webm)"}
        <input type="file" accept="video/*" className="hidden" onChange={handleChange} disabled={uploading} />
      </label>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
