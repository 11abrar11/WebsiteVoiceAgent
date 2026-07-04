import { motion } from "framer-motion";

interface PortfolioFilterProps {
  activeFilter: string;
  onFilterChange: (filter: string) => void;
}

const filters = [
  { id: 'all', label: 'All Work', category: '*' },
  { id: 'banners', label: 'Banner Ads', category: 'banners' },
  { id: 'eblast', label: 'E-blasts', category: 'eblast' },
  { id: 'flyers', label: 'Flyers', category: 'flyers' },
  { id: 'magazine', label: 'Magazine', category: 'magazine' },
  { id: 'packaging', label: 'Packaging', category: 'packaging' },
  { id: 'social', label: 'Social Posts', category: 'social' },
  { id: 'video', label: 'Video', category: 'video' }
];

export default function PortfolioFilter({ activeFilter, onFilterChange }: PortfolioFilterProps) {
  return (
    <div className="flex flex-wrap justify-center gap-2 mb-12">
      {filters.map((filter) => (
        <motion.button
          key={filter.id}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onFilterChange(filter.category === '*' ? 'All' : filter.category)}
          className={`px-6 py-2 rounded-full border-2 transition-all duration-300 ${
            activeFilter === (filter.category === '*' ? 'All' : filter.category)
              ? "bg-primary text-white border-primary shadow-[0_0_15px_rgba(0,166,81,0.5)]"
              : "bg-transparent text-foreground border-primary/20 hover:border-primary/50"
          }`}
          data-testid={`button-filter-${filter.id}`}
        >
          {filter.label}
        </motion.button>
      ))}
    </div>
  );
}
