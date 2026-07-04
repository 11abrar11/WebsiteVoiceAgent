import { Link, useLocation } from "wouter";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import logoFull from "@assets/logo-full.svg";
import logoIcon from "@assets/logo-main.svg";


const links = [
  { href: "/", label: "Home" },
  { href: "/services", label: "Services" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
  { href: "/voice-agent", label: "AI Voice Agent" },
];


interface NavbarProps {
  variant?: "default" | "dark-text";
  stickyVariant?: "light" | "dark";
  forceDarkText?: boolean;
  customLogo?: string;
}

export function Navbar({ variant = "default", stickyVariant = "light", forceDarkText = false, customLogo }: NavbarProps) {

  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [location] = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled
        ? (stickyVariant === "dark" 
            ? "bg-black/95 backdrop-blur-md border-b border-white/10 py-3 shadow-lg" 
            : "bg-white/95 backdrop-blur-md border-b border-gray-100 py-3 shadow-sm")
        : (variant === "dark-text" ? "bg-black/95 py-6" : "bg-transparent py-6")
        }`}

    >
      <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
        <Link href="/">
          <div className="cursor-pointer flex items-center gap-3">
            <img
              src={customLogo ? customLogo : ((scrolled && stickyVariant !== "dark") ? logoIcon : logoFull)}
              alt="PP5 Logo"
              className={`transition-all duration-300 ${scrolled ? "h-8" : "h-12"}`}
            />
          </div>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-8">
          {links.map((link) => (
            <Link key={link.href} href={link.href}>
              <span className={`cursor-pointer text-sm font-medium transition-colors hover:text-primary ${location === link.href
                ? "text-primary"
                : (forceDarkText || (scrolled && stickyVariant !== "dark") ? "text-black/80" : "text-white/80")
                }`}>
                {link.label}
              </span>
            </Link>
          ))}
          <Link href="/contact">
            <button className="px-5 py-2 bg-primary text-white text-sm font-semibold rounded-full hover:bg-primary/90 transition-all hover:scale-105 active:scale-95 shadow-lg shadow-primary/20">
              Get Started
            </button>
          </Link>
        </div>

        {/* Mobile Toggle */}
        <button
          className={`md:hidden p-2 ${scrolled && stickyVariant !== "dark" ? "text-black" : "text-white"}`}
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-black border-b border-white/10 overflow-hidden"
          >
            <div className="container mx-auto px-4 py-6 flex flex-col gap-4">
              {links.map((link) => (
                <Link key={link.href} href={link.href}>
                  <span
                    className="text-lg font-medium text-white/80 hover:text-primary block py-2"
                    onClick={() => setIsOpen(false)}
                  >
                    {link.label}
                  </span>
                </Link>
              ))}
              <Link href="/contact">
                <button
                  className="w-full mt-4 px-5 py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary/90"
                  onClick={() => setIsOpen(false)}
                >
                  Get Started
                </button>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
