import { Link } from "wouter";
import { MapPin, Mail, Phone } from "lucide-react";
import logoFull from "@assets/logo-white.svg";

export function Footer() {
  return (
    <footer className="bg-black text-white pt-20 pb-10 border-t border-white/10">
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-16">

          {/* Brand */}
          <div className="lg:col-span-2 space-y-6">
            <p className="text-gray-400 leading-relaxed">
              At the intersection of design, technology, and strategy, we craft digital experiences that drive growth.
            </p>
            <img src={logoFull} alt="PP5 Logo" className="h-12" />
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-lg font-bold font-display mb-6">Company</h4>
            <ul className="space-y-4">
              {[
                { label: 'About', href: '/about' },
                { label: 'Services', href: '/services' },
                { label: 'Portfolio', href: '/portfolio' },
                { label: 'Case Studies', href: '/case-study/dfw-airport-parking' },
                { label: 'AI Voice Agent', href: '/voice-agent' },
                { label: 'Contact', href: '/contact' },
              ].map((item) => (
                <li key={item.label}>
                  <Link href={item.href}>
                    <span className="text-gray-400 hover:text-primary transition-colors cursor-pointer">
                      {item.label}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Services — no links, no hover */}
          <div>
            <h4 className="text-lg font-bold font-display mb-6">Services</h4>
            <ul className="space-y-4">
              {['Brand Identity', 'Print & Digital Graphics', 'Animation', 'Digitization', 'BPO Services'].map((item) => (
                <li key={item}>
                  <span className="text-gray-400 text-sm">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-lg font-bold font-display mb-6">Get in Touch</h4>
            <ul className="space-y-4">
              <li className="flex items-start gap-3 text-gray-400">
                <MapPin className="text-primary shrink-0 mt-1" size={18} />
                <span className="text-sm">1st Floor, No 62, HC Srikantiah Layout,<br />AC Post, Bangalore 560045</span>
              </li>
              <li className="flex items-center gap-3 text-gray-400">
                <Mail className="text-primary shrink-0" size={18} />
                <a href="mailto:support@pp5mediasolutions.com" className="hover:text-white text-sm">support@pp5mediasolutions.com</a>
              </li>
              <li className="flex items-center gap-3 text-gray-400">
                <Phone className="text-primary shrink-0" size={18} />
                <a href="tel:+919343385042" className="hover:text-white text-sm">+91 93433 85042</a>
              </li>
            </ul>
          </div>

        </div>

        <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-center items-center gap-4 text-sm text-gray-500 text-center">
          <p>© {new Date().getFullYear()} PP5 Agency. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
