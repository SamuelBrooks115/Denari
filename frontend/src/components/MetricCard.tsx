import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  className?: string;
}

export const MetricCard = ({ title, value, subtitle, className }: MetricCardProps) => {
  return (
    <Card className={cn("shadow-soft hover:shadow-elevated transition-shadow", className)}>
      <CardContent className="p-6 space-y-2">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        <p className="text-3xl md:text-4xl font-bold text-primary">{value}</p>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </CardContent>
    </Card>
  );
};
