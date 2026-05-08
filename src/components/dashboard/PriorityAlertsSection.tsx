import useEmblaCarousel from 'embla-carousel-react';
import Autoplay from 'embla-carousel-autoplay';
import { Scholarship } from '@/types/scholarship';
import { AlertTriangle, Clock, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { calculateDaysUntilDeadline } from '@/utils/scholarshipUtils';
import { motion } from 'framer-motion';

interface PriorityAlertsSectionProps {
  urgentScholarships: Scholarship[];
}

export const PriorityAlertsSection = ({ urgentScholarships }: PriorityAlertsSectionProps) => {
  const navigate = useNavigate();
  const [emblaRef, emblaApi] = useEmblaCarousel({ 
    align: 'start', 
    loop: true,
    skipSnaps: false
  }, [Autoplay({ delay: 5000, stopOnInteraction: true })]);

  const scrollPrev = () => emblaApi && emblaApi.scrollPrev();
  const scrollNext = () => emblaApi && emblaApi.scrollNext();

  if (urgentScholarships.length === 0) return null;

  return (
    <section className="mb-10 relative">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 animate-pulse">
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-foreground">Priority Alerts</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="flex h-2 w-2 rounded-full bg-red-500 animate-ping" />
              <span className="text-sm font-medium text-red-500">
                {urgentScholarships.length} Action Required
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            className="rounded-full w-8 h-8 border-border hover:bg-accent"
            onClick={scrollPrev}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="rounded-full w-8 h-8 border-border hover:bg-accent"
            onClick={scrollNext}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="overflow-hidden" ref={emblaRef}>
        <div className="flex gap-4">
          {urgentScholarships.map((scholarship) => {
            const daysLeft = calculateDaysUntilDeadline(scholarship.deadline);
            const scoreNum = Math.round(scholarship.match_score || 0);

            return (
              <div
                key={scholarship.id}
                className="flex-[0_0_100%] min-w-0 md:flex-[0_0_45%] lg:flex-[0_0_32%]"
              >
                <motion.div
                  whileHover={{ y: -4 }}
                  className="h-full group relative overflow-hidden rounded-2xl border border-red-200/50 bg-gradient-to-br from-red-50/50 to-white dark:border-red-900/20 dark:from-red-950/20 dark:to-slate-900/50 p-6 transition-all hover:shadow-xl dark:hover:shadow-red-900/10"
                >
                  <div className="absolute -top-6 -right-6 opacity-[0.03] group-hover:opacity-[0.07] transition-opacity">
                    <Clock className="w-32 h-32 text-red-500" />
                  </div>

                  <div className="relative z-10 flex flex-col h-full">
                    <div className="flex justify-between items-start mb-4 gap-2">
                      <div className="flex flex-wrap gap-2">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-100/80 dark:bg-red-900/40 text-[11px] font-bold text-red-600 dark:text-red-400 backdrop-blur-md border border-red-200/50 dark:border-red-800/30 whitespace-nowrap">
                          <Clock className="w-3.5 h-3.5" />
                          Expires in {daysLeft} days
                        </span>
                      </div>
                      <span className="font-black text-xl text-green-600 dark:text-green-400 drop-shadow-sm whitespace-nowrap">
                        {scholarship.amount_display === "Negotiable" ? "Negotiable" : scholarship.amount_display}
                      </span>
                    </div>

                    <h3 className="font-extrabold text-xl mb-2 line-clamp-1 group-hover:text-red-500 transition-colors tracking-tight">
                      {scholarship.name}
                    </h3>
                    <p className="text-sm font-medium text-muted-foreground mb-6 line-clamp-2 leading-relaxed opacity-80">
                      {scholarship.organization}
                    </p>

                    <div className="mt-auto flex items-center justify-between pt-4 border-t border-red-100/50 dark:border-red-900/20">
                      <div className="flex flex-col">
                        <span className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground opacity-60 mb-0.5">
                          Match Affinity
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-black text-foreground">{scoreNum}%</span>
                          <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                            {scholarship.match_tier || "High Match"}
                          </span>
                        </div>
                      </div>
                      
                      <Button
                        size="sm"
                        className="rounded-xl bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/20 border-none px-4 font-bold h-9 group/btn transition-transform active:scale-95"
                        onClick={() => navigate(`/opportunity/${scholarship.id}`)}
                      >
                        Action
                        <ArrowRight className="w-4 h-4 ml-1.5 transition-transform group-hover/btn:translate-x-1" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
