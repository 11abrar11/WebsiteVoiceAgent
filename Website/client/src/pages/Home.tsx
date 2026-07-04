import { useRef, useEffect } from "react";
/**
 * Homepage Component
 * - Displays the Hero section with background video
 * - Showcases featured case studies
 * - Highlights agency strengths and call-to-action
 */
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { caseStudies } from "@/utils/case-studies";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, Zap } from "lucide-react";
import { Link } from "wouter";
import Typewriter from 'typewriter-effect';

import heroIllustration from "@/assets/hero-illustration.png";
import { SEO } from "@/components/SEO";

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null);

  // Robust Autoplay for Mobile Browsers
  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      // Force muted property and check for playsinline
      video.muted = true;
      video.setAttribute('muted', '');
      video.setAttribute('webkit-playsinline', 'true');
      video.setAttribute('playsinline', 'true');
      
      const attemptPlay = () => {
        video.play().catch(error => {
          console.warn("Hero video autoplay failed:", error);
        });
      };

      // Try playing immediately
      attemptPlay();

      // Fallback: Try again when metadata has loaded
      video.addEventListener('loadedmetadata', attemptPlay);
      return () => video.removeEventListener('loadedmetadata', attemptPlay);
    }
  }, []);

  return (
    <div className="min-h-screen bg-white">
      <SEO
        title="PP5 Media Solutions | Premier Creative & Digital Agency"
        description="PP5 is a premier advertising agency specializing in design, technology, and strategy. We transform brands into industry leaders through innovative digital solutions. Based in Bangalore, serving clients worldwide."
        canonical="/"
        keywords="creative agency, digital agency, branding, graphic design, advertising, Bangalore, PP5 Media Solutions"
      />
      <Navbar />

      {/* 
        Hero Section 
        - Features a side-aligned background video
        - Uses a typewriter effect for the main headline
        - Interactive buttons for navigation
      */}
      <section className="relative min-h-screen flex items-center pt-20 pb-16 md:pb-0 overflow-hidden bg-black">

        {/* 
          Background Video 
          - Managed by .gitignore to ensure optimized mp4 is uploaded
          - Positioned on the right with an opacity fade
        */}
        <video
          ref={videoRef}
          src="/walk.mp4"
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-y-0 right-0 w-full md:w-1/2 object-cover opacity-60 md:opacity-100 transition-opacity duration-1000 z-0"
          style={{ objectPosition: 'center' }}
        />

        {/* 
          Gradient Overlay
          - Full black on mobile to ensure text readability
          - Desktop: Creates a seamless transition from the solid black text area 
          - to the transparent video area on the right.
        */}
        <div className="absolute inset-0 bg-black/50 md:bg-transparent z-[1]" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/20 to-black md:bg-gradient-to-r md:from-black md:via-black md:to-transparent z-[2]" />

        <div className="container mx-auto px-4 md:px-6 relative z-10">
          <div className="max-w-4xl">
            {/* Animated Badge */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: false, margin: "-50px" }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 text-primary text-sm font-semibold mb-6 border border-white/5 backdrop-blur-sm"
            >
              <Zap size={16} /> Digital Excellence Redefined
            </motion.div>

            {/* Main Headline with Typewriter effect */}
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: false, margin: "-50px" }}
              className="text-5xl md:text-8xl font-black font-display text-white mb-6 leading-[0.9] tracking-tighter"
            >
              We Craft Digital <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-green-400">
                <Typewriter
                  options={{
                    strings: ['Masterpieces.', 'Experiences.', 'Solutions.', 'Impact.'],
                    autoStart: true,
                    loop: true,
                  }}
                />
              </span>
            </motion.h1>

            {/* Agency description sub-text */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="text-xl text-gray-400 mb-8 md:mb-10 max-w-2xl leading-relaxed"
            >
              PP5 is a premier advertising agency specializing in design, technology, and strategy. We transform brands into industry leaders through innovative digital solutions.
            </motion.p>

            {/* Primary & Secondary CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4 mt-4 sm:mt-0"
            >
              <Link href="/services">
                <button className="w-full sm:w-auto px-8 py-4 bg-primary text-white font-bold rounded-lg hover:bg-green-600 transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-1 flex items-center justify-center gap-2">
                  Explore Services <ArrowRight size={20} />
                </button>
              </Link>
              <Link href="/contact">
                <button className="w-full sm:w-auto px-8 py-4 bg-transparent border-2 border-white/20 text-white font-bold rounded-lg hover:bg-white/10 transition-all hover:-translate-y-1">
                  Contact Us
                </button>
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* 
        Stats/Social Proof Section 
        - Displays a grayscale list of clients/brands
        - Becomes colorful on hover
      */}
      <section className="py-12 border-b border-gray-100 bg-white">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap justify-center md:justify-between items-center gap-8 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
            {['Goodwill', 'ABI', 'Media Marketing', 'Grace Media', 'DFW Airport'].map((client, i) => (
              <span key={i} className="text-2xl font-bold font-display text-gray-400">{client}</span>
            ))}
          </div>
        </div>
      </section>

      {/* 
        Featured Case Studies Section 
        - Pulls the first 2 projects from the case studies utility
        - Uses Framer Motion for scroll-triggered entry animations
      */}
      <section className="py-24 bg-gray-50">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-sm font-bold tracking-widest text-primary uppercase mb-3">Our Work</h2>
            <h3 className="text-4xl md:text-5xl font-bold font-display text-gray-900 mb-6">Featured Case Studies</h3>
            <p className="text-lg text-gray-600">
              Explore how we've helped leading brands achieve digital transformation and measurable growth.
            </p>
          </div>

          {/* Grid display of case studies */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
            {caseStudies.slice(0, 2).map((study, index) => (
              <motion.div
                key={study.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: false, margin: "-50px" }}
                className="group relative bg-white rounded-3xl overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300 border border-gray-100"
              >
                {/* Project Image backdrop */}
                <div className="aspect-[3/2] overflow-hidden">
                  <img
                    src={study.image}
                    alt={study.title}
                    loading="lazy"
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                  {/* Subtle dark overlay to make text pop */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
                </div>

                {/* Project Brief Info */}
                <div className="absolute inset-x-0 bottom-0 p-8 text-white">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="px-3 py-1 bg-primary/90 text-xs font-bold uppercase tracking-wider rounded-full">
                      {study.category}
                    </span>
                  </div>
                  <h3 className="text-xl md:text-3xl font-bold font-display mb-4 md:mb-6 relative inline-block">
                    <span className="relative">
                      {study.title}
                      {/* Interactive underline animation */}
                      <span className="absolute -bottom-1 left-0 h-[2px] w-0 bg-primary transition-all duration-500 group-hover:w-full rounded-full" />
                    </span>
                  </h3>
                  <Link href={`/case-study/${study.slug}`}>
                    <button className="flex items-center text-white font-bold group-hover:text-primary transition-colors duration-300">
                      View Case Study <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 
        Strengths/Features Section 
        - Dark background to provide visual contrast
        - Highlights the "Evolve Brands" philosophy
      */}
      <section className="py-24 bg-black text-white overflow-hidden">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            {/* Text Side */}
            <div className="lg:w-1/2">
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: false, margin: "-100px" }}
              >
                <h2 className="text-sm font-bold tracking-widest text-primary uppercase mb-3">Why Choose Us</h2>
                <h3 className="text-4xl md:text-5xl font-bold font-display mb-8">
                  We Don't Just Build.<br />We Evolve Brands.
                </h3>
                {/* Benefit List */}
                <div className="space-y-6">
                  {[
                    "Strategic Thinking First: We analyze before we design.",
                    "Pixel-Perfect Execution: Obsessive attention to detail.",
                    "Data-Driven Results: Decisions backed by analytics.",
                    "24/5 Dedicated Support: We are always here for you."
                  ].map((item, i) => (
                    <div key={i} className="flex items-start gap-4">
                      <div className="p-1 rounded-full bg-primary/20 text-primary mt-1">
                        <CheckCircle2 size={18} />
                      </div>
                      <p className="text-lg text-gray-300">{item}</p>
                    </div>
                  ))}
                </div>
                <Link href="/about">
                  <button className="mt-10 px-8 py-3 bg-white text-black font-bold rounded-lg hover:bg-gray-200 transition-colors">
                    Learn More About Us
                  </button>
                </Link>
              </motion.div>
            </div>
            {/* Visual Side */}
            <div className="lg:w-1/2 relative">
              <div className="relative z-10 rounded-2xl overflow-hidden border border-white/10 shadow-2xl">
                <img
                  src={heroIllustration}
                  alt="Team collaboration"
                  loading="lazy"
                  className="w-full h-auto transform hover:scale-105 transition-transform duration-700"
                />
              </div>
              {/* Abstract decorative blurs for premium feel */}
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary/20 rounded-full blur-3xl" />
              <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl" />
            </div>
          </div>
        </div>
      </section>

      {/* 
        CTA Section (Final Hook)
        - Bright background to grab attention before the footer
        - Encourages users to start a project
      */}
      <section className="py-24 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10" />
        <div className="container mx-auto px-4 text-center relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold font-display text-white mb-6">Ready to Transform Your Business?</h2>
          <p className="text-xl text-green-50 mb-10 max-w-2xl mx-auto">
            Let's create something extraordinary together. Schedule a free consultation today.
          </p>
          <Link href="/contact">
            <button className="px-10 py-4 bg-black text-white text-lg font-bold rounded-full hover:bg-gray-900 transition-all shadow-xl hover:shadow-2xl hover:-translate-y-1 animate-pulse-green">
              Start Your Project
            </button>
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
