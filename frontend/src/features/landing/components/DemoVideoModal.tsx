import { X } from "lucide-react";
import { useTranslation } from "react-i18next";

interface DemoVideoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DemoVideoModal({ isOpen, onClose }: DemoVideoModalProps) {
  const { t } = useTranslation();
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative bg-white rounded-2xl shadow-2xl w-[90vw] max-w-[1000px] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-semibold text-[#1F2937]">{t("landing.demoVideo")}</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label={t("landing.demoModal.close")}
          >
            <X className="w-6 h-6 text-[#6A737D]" />
          </button>
        </div>

        {/* Video Container */}
        <div className="relative w-full" style={{ paddingBottom: "56.25%" }}>
          <iframe
            className="absolute inset-0 w-full h-full"
            src="https://www.youtube.com/embed/761ae_KDg_Q"
            title="LiveNote Demo Video"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          ></iframe>
        </div>

        {/* Footer */}
        <div className="p-6 bg-gray-50">
          <p className="text-sm text-[#6B7280] text-center">{t("landing.demoModal.footer")}</p>
        </div>
      </div>
    </div>
  );
}
