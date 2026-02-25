"use client";

interface ProcessingStatusProps {
  status: string;
  progress?: number;
}

export default function ProcessingStatus({
  status,
  progress = 0,
}: ProcessingStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case "completed":
        return "bg-green-500 text-green-100";
      case "processing":
        return "bg-blue-500 text-blue-100";
      case "failed":
        return "bg-red-500 text-red-100";
      default:
        return "bg-yellow-500 text-yellow-100";
    }
  };

  const getStatusMessage = () => {
    switch (status) {
      case "completed":
        return "✓ Meeting Processed";
      case "processing":
        return "⏳ Processing...";
      case "failed":
        return "✗ Processing Failed";
      default:
        return "⟳ Pending";
    }
  };

  return (
    <div className="w-full space-y-3">
      <div
        className={`px-4 py-3 rounded-xl ${getStatusColor()} font-semibold text-sm flex items-center justify-between`}
      >
        <span>{getStatusMessage()}</span>
        {status === "processing" && (
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
        )}
      </div>

      {status === "processing" && progress > 0 && (
        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      )}
    </div>
  );
}