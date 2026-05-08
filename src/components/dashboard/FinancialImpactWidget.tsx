import { DollarSign, TrendingUp } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DashboardStats } from '@/types/scholarship';
import { formatCurrency } from '@/utils/scholarshipUtils';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface FinancialImpactWidgetProps {
  stats: DashboardStats;
}

export const FinancialImpactWidget = ({ stats }: FinancialImpactWidgetProps) => {
  const data = [
    { name: 'Not Yet Applied', value: stats.total_value * 0.7, color: 'hsl(var(--primary))' },
    { name: 'Applied & Pending', value: stats.total_value * 0.25, color: 'hsl(var(--info))' },
    { name: 'Won', value: stats.total_value * 0.05, color: 'hsl(var(--success))' },
  ];

  const potentialWinnings = Math.round(stats.total_value * 0.3);

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <DollarSign className="h-5 w-5 text-success" />
        Financial Impact
      </h3>

      <div className="mb-6 relative">
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => formatCurrency(value)}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div className="text-lg sm:text-xl md:text-2xl font-bold text-foreground whitespace-nowrap">
              {stats.total_value >= 1000000 
                ? `$${(stats.total_value / 1000000).toFixed(1)}M`
                : formatCurrency(stats.total_value)
              }
            </div>
            <div className="text-xs text-muted-foreground">Total Value</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="text-center p-3 rounded-lg bg-primary/5">
          <div className="text-lg font-bold text-foreground">{stats.opportunities_matched}</div>
          <div className="text-xs text-muted-foreground">Available</div>
        </div>
        <div className="text-center p-3 rounded-lg bg-info/5">
          <div className="text-lg font-bold text-foreground">{stats.applications_started}</div>
          <div className="text-xs text-muted-foreground">Applied</div>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-success/5 border border-success/20 mb-4">
        <div className="flex items-start gap-2">
          <TrendingUp className="h-4 w-4 text-success shrink-0 mt-0.5" />
          <div className="text-sm text-foreground/90">
            Apply to your top 10 matches to potentially win <strong className="text-success">{formatCurrency(potentialWinnings)}</strong>!
          </div>
        </div>
      </div>

      <Button variant="outline" className="w-full" size="sm">
        See Full Impact Report
      </Button>
    </Card>
  );
};
