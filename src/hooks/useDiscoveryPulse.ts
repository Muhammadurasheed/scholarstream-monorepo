
import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

export interface DiscoveryMission {
    mission_id: string;
    target: string;
    status: 'active' | 'completed';
    timestamp: number;
    label: string;
    found_count?: number;
    completed_at?: number;
}

export const useDiscoveryPulse = () => {
    const [pulse, setPulse] = useState<{
        status: 'active' | 'idle';
        missions: DiscoveryMission[];
    }>({ status: 'idle', missions: [] });

    useEffect(() => {
        const fetchPulse = async () => {
            try {
                const data = await apiService.getDiscoveryPulse();
                setPulse(data);
            } catch (error) {
                console.error('Failed to fetch discovery pulse', error);
            }
        };

        // Initial fetch
        fetchPulse();

        // Poll every 5 seconds for real-time vibe
        const interval = setInterval(fetchPulse, 5000);

        return () => clearInterval(interval);
    }, []);

    return pulse;
};
