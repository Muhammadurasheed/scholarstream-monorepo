
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radar, Search, CheckCircle, Zap } from 'lucide-react';
import { useDiscoveryPulse } from '@/hooks/useDiscoveryPulse';

export const DiscoveryPulseIndicator: React.FC = () => {
    const { status, missions } = useDiscoveryPulse();

    if (status === 'idle' && missions.length === 0) return null;

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end space-y-2 pointer-events-none">
            <AnimatePresence>
                {missions.map((mission) => (
                    <motion.div
                        key={mission.mission_id}
                        initial={{ opacity: 0, x: 50, scale: 0.9 }}
                        animate={{ opacity: 1, x: 0, scale: 1 }}
                        exit={{ opacity: 0, x: 20, scale: 0.9 }}
                        className={`flex items-center space-x-3 px-4 py-3 rounded-2xl shadow-2xl backdrop-blur-xl border ${mission.status === 'active'
                                ? 'bg-blue-500/10 border-blue-500/20 text-blue-400'
                                : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                            }`}
                    >
                        <div className="relative">
                            {mission.status === 'active' ? (
                                <motion.div
                                    animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                                >
                                    <Radar className="w-5 h-5" />
                                </motion.div>
                            ) : (
                                <CheckCircle className="w-5 h-5" />
                            )}
                            {mission.status === 'active' && (
                                <motion.div
                                    className="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full"
                                    animate={{ scale: [1, 1.5, 1] }}
                                    transition={{ duration: 1, repeat: Infinity }}
                                />
                            )}
                        </div>

                        <div className="flex flex-col">
                            <span className="text-sm font-semibold tracking-tight">
                                {mission.status === 'active' ? 'Live Discovery' : 'Capture Success'}
                            </span>
                            <span className="text-[11px] opacity-70 font-medium truncate max-w-[200px]">
                                {mission.label}
                            </span>
                        </div>

                        {mission.status === 'active' && (
                            <div className="flex space-x-1 pl-2">
                                {[0, 1, 2].map((i) => (
                                    <motion.div
                                        key={i}
                                        className="w-1 h-3 bg-blue-400/30 rounded-full"
                                        animate={{ height: [4, 12, 4] }}
                                        transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.1 }}
                                    />
                                ))}
                            </div>
                        )}
                    </motion.div>
                ))}
            </AnimatePresence>

            {/* Global Status Bar */}
            {status === 'active' && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-zinc-900/80 border border-white/5 py-1 px-3 rounded-full flex items-center space-x-2 shadow-sm"
                >
                    <Zap className="w-3 h-3 text-yellow-400 animate-pulse" />
                    <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">
                        Sentinel Active
                    </span>
                </motion.div>
            )}
        </div>
    );
};
