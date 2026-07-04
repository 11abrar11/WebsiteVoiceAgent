import { motion } from "framer-motion";
import * as Icons from "lucide-react";
import { type Service } from "@shared/schema";
import Tilt from 'react-parallax-tilt';
import { useDeviceFeatures } from "@/hooks/useDeviceFeatures";

interface ServiceCardProps {
  service: Service;
  index: number;
}

export function ServiceCard({ service, index }: ServiceCardProps) {
  const { isMobile, prefersReducedMotion } = useDeviceFeatures();
  const IconComponent = (Icons as any)[service.icon] || Icons.Zap;

  const tiltDisabled = isMobile || prefersReducedMotion;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      viewport={{ once: false, margin: "-50px" }}
      className="h-full"
    >
      <Tilt
        tiltMaxAngleX={tiltDisabled ? 0 : 10}
        tiltMaxAngleY={tiltDisabled ? 0 : 10}
        glareEnable={!tiltDisabled}
        glareMaxOpacity={0.1}
        scale={tiltDisabled ? 1 : 1.02}
        className="h-full"
      >
        <div className="group relative p-8 rounded-2xl bg-white border border-gray-100 hover:border-primary/30 transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 overflow-hidden h-full">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-full -mr-8 -mt-8 transition-all group-hover:bg-primary/10 group-hover:scale-110" />

          <div className="relative z-10">
            <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:bg-primary group-hover:text-white transition-colors duration-300">
              <IconComponent size={28} />
            </div>

            <h3 className="text-xl font-bold font-display text-gray-900 mb-3 group-hover:text-primary transition-colors">
              {service.title}
            </h3>

            <p className="text-gray-600 leading-relaxed mb-6 text-sm">
              {service.description}
            </p>
          </div>
        </div>
      </Tilt>
    </motion.div>
  );
}
