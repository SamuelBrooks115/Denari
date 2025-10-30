import { Hero } from "@/components/Hero";
import { MetricCard } from "@/components/MetricCard";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export default function Valuation() {
  const metrics = [
    { title: "Metric 1", value: "92%", subtitle: "Accuracy rate" },
    { title: "Metric 2", value: "45min", subtitle: "Average time saved" },
    { title: "Metric 3", value: "15+", subtitle: "Industry templates" },
    { title: "Metric 4", value: "99.9%", subtitle: "Uptime guarantee" },
  ];

  return (
    <div className="min-h-screen">
      <Hero title="DENARI" subtitle="Why Valuation is Important" />

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto mb-12">
            <p className="text-lg text-center text-muted-foreground">
              Accurate valuation is the cornerstone of sound investment decisions. Denari improves the valuation
              process by combining automation with industry best practices, ensuring you have reliable models that
              stand up to scrutiny.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {metrics.map((metric, index) => (
              <MetricCard key={index} {...metric} />
            ))}
          </div>

          <div className="text-center">
            <Link to="/login">
              <Button size="lg" className="bg-primary hover:bg-primary/90">
                Start Project Now
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
