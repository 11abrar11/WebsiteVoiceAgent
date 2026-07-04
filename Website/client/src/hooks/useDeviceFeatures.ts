import { useState, useEffect } from "react";

/**
 * Custom hook to detect device features
 * - isMobile: Detects typical touch devices or small screens
 * - prefersReducedMotion: Detects OS-level accessibility settings
 */
export function useDeviceFeatures() {
  const [features, setFeatures] = useState({
    isMobile: false,
    prefersReducedMotion: false,
  });

  useEffect(() => {
    // Media query to check if the device is a touch screen
    const mobileQuery = window.matchMedia("(pointer: coarse), (max-width: 768px)");
    
    // Media query to check OS-level motion reduction settings
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    const updateFeatures = () => {
      setFeatures({
        isMobile: mobileQuery.matches,
        prefersReducedMotion: motionQuery.matches,
      });
    };

    // Initial check
    updateFeatures();

    // Event listeners
    mobileQuery.addEventListener("change", updateFeatures);
    motionQuery.addEventListener("change", updateFeatures);

    return () => {
      mobileQuery.removeEventListener("change", updateFeatures);
      motionQuery.removeEventListener("change", updateFeatures);
    };
  }, []);

  return features;
}
