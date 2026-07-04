import { motion } from "framer-motion";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Play } from "lucide-react";
import type { PortfolioItem } from "@/utils/portfolio";

interface PortfolioCardProps {
  item: PortfolioItem;
  onOpen: (item: PortfolioItem) => void;
}

export default function PortfolioCard({ item, onOpen }: PortfolioCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const hoverText = item.hoverText || `${item.category.charAt(0).toUpperCase() + item.category.slice(1)} - ${item.client || 'Portfolio Item'}`;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.3 }}
      className="relative group cursor-pointer overflow-visible mb-6"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onOpen(item)}
      data-testid={`card-portfolio-${item.id}`}
    >
      <div className="rounded-xl overflow-hidden bg-card border border-border/50 relative">
        <motion.img
          src={item.thumbnail}
          alt={item.title}
          loading="lazy"
          className="w-full h-auto object-cover transition-all duration-500"
          animate={{
            scale: isHovered ? 1.08 : 1,
            filter: isHovered ? "grayscale(0%)" : "grayscale(20%)"
          }}
        />

        {/* Video Play Icon Overlay */}
        {item.video && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: isHovered ? 1 : 0.9, scale: isHovered ? 1 : 0.9 }}
            className="absolute inset-0 flex items-center justify-center bg-black/30"
          >
            <div className="w-16 h-16 rounded-full bg-primary/90 flex items-center justify-center shadow-lg">
              <Play className="w-8 h-8 text-white ml-1" fill="white" />
            </div>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: isHovered ? 1 : 0, y: isHovered ? 0 : 20 }}
          className="absolute inset-0 bg-primary/90 flex flex-col justify-end p-6 text-white"
        >
          {item.client && (
            <p className="text-sm font-medium opacity-80 mb-1">{item.client}</p>
          )}
          <h3 className="text-xl font-bold mb-2">{item.title}</h3>
          <p className="text-sm italic mb-4">{hoverText}</p>
          <div className="flex flex-wrap gap-2">
            {item.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-white border-white/50 bg-white/10 no-default-hover-elevate">
                {tag}
              </Badge>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
