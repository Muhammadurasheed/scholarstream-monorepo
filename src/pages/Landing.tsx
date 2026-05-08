import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll } from 'framer-motion';
import { ArrowRight, Sparkles, Zap, Shield, Globe, Search, Bell, GraduationCap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ssLogo from '@/asset/ss_logo.png';

const FloatingNav = () => {
  const { scrollY } = useScroll();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    return scrollY.onChange((latest) => {
      setIsScrolled(latest > 50);
    });
  }, [scrollY]);

  return (
    <motion.nav
      className={`fixed top-0 left-0 right-0 z-50 flex justify-center py-4 transition-all duration-300 ${isScrolled ? 'py-4' : 'py-6'}`}
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className={`
                flex items-center justify-between px-6 
                ${isScrolled ? 'w-[80vw] h-14 bg-background/80 backdrop-blur-xl border border-white/10 shadow-lg' : 'w-full max-w-7xl bg-transparent'} 
                rounded-full transition-all duration-500 ease-out
            `}>
        <div className="flex items-center gap-2">
          <img src={ssLogo} alt="ScholarStream Logo" className="w-8 h-8 object-contain" />
          <span className="font-semibold text-lg tracking-tight hidden sm:block">ScholarStream</span>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="rounded-full hover:bg-white/5" asChild>
            <Link to="/login">Sign in</Link>
          </Button>
          <Button size="sm" className="rounded-full bg-foreground text-background hover:bg-foreground/90 transition-all font-medium px-6" asChild>
            <Link to="/signup">Get Started</Link>
          </Button>
        </div>
      </div>
    </motion.nav>
  );
};

const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center px-4 overflow-hidden pt-20">
      {/* Background Gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-primary/20 rounded-full blur-[120px] animate-pulse-glow" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-500/20 rounded-full blur-[120px] delay-1000 animate-pulse-glow" />
      </div>

      <div className="absolute inset-0 bg-grid opacity-[0.03] z-0" />

      <div className="relative z-10 max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-8"
        >
          <img src={ssLogo} alt="Logo" className="w-5 h-5 object-contain" />
          <span className="text-sm font-medium bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
            The future of opportunity
          </span>
        </motion.div>

        <motion.h1
          className="text-5xl sm:text-7xl md:text-8xl font-semibold tracking-tighter leading-[1.1] mb-8"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        >
          Organizing the world's <br className="hidden md:block" />
          <span className="text-gradient">opportunities</span>
        </motion.h1>

        <motion.p
          className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
        >
          ScholarStream makes global funding universally accessible and useful.
          From scholarships to hackathons, we connect you with the resources to build what's next.
        </motion.p>

        <motion.div
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <Button size="lg" className="h-14 px-8 rounded-full text-lg shadow-glow hover:scale-105 transition-transform duration-300" asChild>
            <Link to="/signup">
              Explore Opportunities
              <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="h-14 px-8 rounded-full text-lg border-white/20 hover:bg-white/5 backdrop-blur-sm" asChild>
            <Link to="/login">
              View Demo
            </Link>
          </Button>
        </motion.div>
      </div>

      {/* Floating Elements */}
      <motion.div
        className="absolute top-1/4 left-10 p-4 rounded-2xl glass-panel hidden lg:block"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.8, duration: 1 }}
      >
        <div className="flex items-center gap-3">
          <div className="bg-green-500/20 p-2 rounded-lg text-green-500">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Match Found</p>
            <p className="font-semibold text-sm">$10,000 STEM Grant</p>
          </div>
        </div>
      </motion.div>

      <motion.div
        className="absolute bottom-1/4 right-10 p-4 rounded-2xl glass-panel hidden lg:block"
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 1, duration: 1 }}
      >
        <div className="flex items-center gap-3">
          <div className="bg-blue-500/20 p-2 rounded-lg text-blue-500">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Application Auto-filled</p>
            <p className="font-semibold text-sm">Review & Submit</p>
          </div>
        </div>
      </motion.div>
    </section>
  );
};

const FeatureCard = ({ icon: Icon, title, description, delay = 0 }: { icon: any, title: string, description: string, delay?: number }) => {
  return (
    <motion.div
      className="group relative p-8 rounded-3xl bg-secondary/30 border border-white/5 hover:bg-secondary/50 transition-colors duration-500 overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative z-10">
        <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
          <Icon className="w-6 h-6 text-primary" />
        </div>
        <h3 className="text-xl font-semibold mb-3">{title}</h3>
        <p className="text-muted-foreground leading-relaxed">
          {description}
        </p>
      </div>
    </motion.div>
  );
};

const FeaturesSection = () => {
  return (
    <section className="py-24 px-4 relative z-10">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <motion.h2
            className="text-3xl md:text-5xl font-bold mb-6 tracking-tight"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            Built for <span className="text-gradient">high performers</span>
          </motion.h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            We've reimagined the scholarship search process from the ground up to be faster, smarter, and more effective.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard
            icon={Search}
            title="Comprehensive Discovery"
            description="Access a massive ecosystem of scholarships, hackathons, grants, and bounties aggregated from thousands of sources."
            delay={0.1}
          />
          <FeatureCard
            icon={Zap}
            title="Smart Matching"
            description="Our AI doesn't just keyword match; it understands your profile to find opportunities you can actually win."
            delay={0.2}
          />
          <FeatureCard
            icon={Shield}
            title="Vetted & Verified"
            description="Every opportunity—whether a $100 bounty or $50k grant—is verified for legitimacy."
            delay={0.3}
          />
          <FeatureCard
            icon={Bell}
            title="Instant Alerts"
            description="Be the first to know about new bug bounties, hackathons, and grants matching your skills."
            delay={0.4}
          />
          <FeatureCard
            icon={Globe}
            title="Global Database"
            description="Access opportunities from over 50 countries, regardless of your citizenship status."
            delay={0.5}
          />
          <FeatureCard
            icon={Sparkles}
            title="Essay Assistant"
            description="Get AI-powered suggestions to improve your essays and increase your chances of winning."
            delay={0.6}
          />
        </div>
      </div>
    </section>
  );
};

const Landing = () => {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden selection:bg-primary/20 selection:text-primary">
      <FloatingNav />
      <HeroSection />
      <FeaturesSection />

      <footer className="py-12 border-t border-white/5 relative z-10">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} ScholarStream. Powered by Google Cloud.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
