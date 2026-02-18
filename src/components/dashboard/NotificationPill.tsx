import { ArrowUp, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

interface NotificationPillProps {
    count: number;
    onClick: () => void;
}

export function NotificationPill({ count, onClick }: NotificationPillProps) {
    return (
        <AnimatePresence>
            {count > 0 && (
                <motion.div
                    initial={{ y: -50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: -50, opacity: 0 }}
                    className="fixed top-24 left-1/2 transform -translate-x-1/2 z-50"
                >
                    <Button
                        onClick={onClick}
                        className="rounded-full shadow-lg bg-blue-600 hover:bg-blue-700 text-white px-6 py-6 border-2 border-white/20 backdrop-blur-md animate-pulse-subtle"
                        size="lg"
                    >
                        <Sparkles className="w-4 h-4 mr-2 text-yellow-300" />
                        <span className="font-semibold text-base">
                            {count} New {count === 1 ? 'Opportunity' : 'Opportunities'} Found
                        </span>
                        <ArrowUp className="w-4 h-4 ml-2" />
                    </Button>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
