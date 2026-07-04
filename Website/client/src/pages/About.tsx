/**
 * About Page Component
 * - Presents the agency's history, mission, and philosophy
 * - Uses Core Values grid and Story sections with animations
 */
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { PageHeader } from "@/components/PageHeader";
import { motion } from "framer-motion";
import { Lightbulb, Heart, Star, Zap } from "lucide-react";
import aboutIllustration from "@/assets/about-illustration.png";
import { SEO } from "@/components/SEO";

/**
 * Data for Core Values section
 * Each item includes a Lucide icon, title, and short description.
 */
const coreValues = [
  {
    icon: Lightbulb,
    title: "Creativity with Purpose",
    desc: "Every design is intentional and results-driven.",
  },
  {
    icon: Heart,
    title: "Client-Centric Approach",
    desc: "We design around your goals, not trends.",
  },
  {
    icon: Star,
    title: "Commitment to Excellence",
    desc: "Delivering high-quality outputs, every time.",
  },
  {
    icon: Zap,
    title: "Innovation First",
    desc: "Staying ahead with evolving technology and ideas.",
  },
];

export default function About() {
  return (
    <div className="min-h-screen bg-white">
      <SEO
        title="About Us — Designing Experiences, Building Brands, Driving Impact"
        description="PP5 Media Solutions is a multidisciplinary creative and technology agency founded in 2018, headquartered in Bangalore. We deliver branding, design, and digital services to clients worldwide including DFW Airport and Goodwill Dallas."
        canonical="/about"
        keywords="about PP5 Media Solutions, creative agency Bangalore, digital agency India, branding agency, design team"
      />
      <Navbar />

      {/* 
        Standardized Header 
        - Sets the tone for the entire page
      */}
      <PageHeader
        title="Designing Experiences. Building Brands. Driving Impact."
        subtitle="PP5 Media Solutions — A multidisciplinary creative and technology agency delivering branding, design, and digital services worldwide."
      />

      {/* ── Who We Are (Intro Section) ── */}
      <section className="py-24">
        <div className="container mx-auto px-4 md:px-6">
          <div className="max-w-4xl mx-auto text-center">
            {/* Animated small label */}
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.5 }}
              className="inline-block text-sm font-semibold tracking-widest text-primary uppercase mb-4"
            >
              Who We Are
            </motion.span>

            {/* Main agency background text */}
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-3xl md:text-4xl font-display font-bold text-gray-900 mb-8 leading-tight"
            >
              Founded in 2018, Headquartered in Bangalore
            </motion.h2>

            {/* Narrative paragraphs with staggered fade-ins */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-xl text-gray-600 leading-relaxed mb-6"
            >
              PP5 Media Solutions is a multidisciplinary creative and technology
              agency delivering branding, design, and digital services to clients
              worldwide.
            </motion.p>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="text-lg text-gray-600 leading-relaxed mb-6"
            >
              We combine creativity, technology, and strategic thinking to help
              brands stand out, connect with audiences, and achieve measurable
              results.
            </motion.p>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="text-lg text-gray-600 leading-relaxed"
            >
              With expertise in branding, UI/UX, digital marketing, e-commerce,
              animation, and multimedia production, we bring together the skills
              and vision to turn ideas into reality.
            </motion.p>
          </div>
        </div>
      </section>

      {/* ── Mission & Vision (The "Why") ── */}
      <section className="py-24 bg-black text-white">
        <div className="container mx-auto px-4 md:px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 max-w-5xl mx-auto">

            {/* Our Mission Card */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.7 }}
              className="relative p-10 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden group"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-primary rounded-l-2xl" />
              <span className="block text-xs font-semibold tracking-widest text-primary uppercase mb-4">
                Our Mission
              </span>
              <p className="text-gray-300 text-lg leading-relaxed italic">
                "To empower businesses with innovative, user-focused creative
                solutions that inspire, engage, and deliver measurable impact
                across every platform and touchpoint."
              </p>
            </motion.div>

            {/* Our Vision Card */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="relative p-10 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden group"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-primary rounded-l-2xl" />
              <span className="block text-xs font-semibold tracking-widest text-primary uppercase mb-4">
                Our Vision
              </span>
              <p className="text-gray-300 text-lg leading-relaxed italic">
                "To be a globally recognized creative and digital partner,
                setting benchmarks in design excellence, innovation, and client
                success."
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Core Values Section ── */}
      <section className="py-24 bg-gray-50">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center mb-16">
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              className="inline-block text-sm font-semibold tracking-widest text-primary uppercase mb-3"
            >
              What Drives Us
            </motion.span>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ delay: 0.1 }}
              className="text-3xl md:text-4xl font-display font-bold text-gray-900"
            >
              Our Core Values
            </motion.h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {coreValues.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                viewport={{ once: false, margin: "-50px" }}
                className="p-8 bg-white rounded-2xl text-center hover:shadow-xl transition-all duration-300 border border-gray-100 hover:border-primary/20 group"
              >
                {/* Icon wrapper with hover state */}
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-primary mx-auto mb-6 group-hover:bg-primary group-hover:text-white transition-all duration-300">
                  <item.icon size={30} />
                </div>
                <h3 className="text-lg font-bold font-display text-gray-900 mb-3">
                  {item.title}
                </h3>
                <p className="text-gray-500 text-sm leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Our Story Section ── */}
      <section className="py-24">
        <div className="container mx-auto px-4 md:px-6">
          <div className="max-w-5xl mx-auto flex flex-col md:flex-row gap-16 items-center">

            {/* High-quality team imagery placeholder (Unsplash) */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.7 }}
              className="md:w-1/2"
            >
              <div className="relative rounded-2xl overflow-hidden shadow-xl group bg-gray-100">
                <img
                  src={aboutIllustration}
                  alt="PP5 team collaborating"
                  loading="lazy"
                  onLoad={(e) => {
                    (e.target as HTMLImageElement).classList.remove('opacity-0');
                  }}
                  className="rounded-2xl object-cover w-full h-80 md:h-auto hover:grayscale transition-all duration-700 opacity-0"
                />
              </div>
            </motion.div>

            {/* Historical narrative */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: false, margin: "-50px" }}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="md:w-1/2 space-y-6"
            >
              <span className="inline-block text-sm font-semibold tracking-widest text-primary uppercase">
                Our Story
              </span>
              <h2 className="text-3xl md:text-4xl font-display font-bold text-gray-900 leading-tight">
                From a Studio in Bangalore to a Trusted Global Partner
              </h2>
              <p className="text-gray-600 text-lg leading-relaxed">
                From a small creative studio in Bangalore to a trusted global
                creative partner, PP5 Media Solutions has grown by combining bold
                ideas, strong execution, and a commitment to client success.
              </p>
              <p className="text-gray-600 text-lg leading-relaxed">
                We've worked with startups, enterprises, and nonprofits across
                industries — delivering solutions that not only look great but
                perform exceptionally.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
