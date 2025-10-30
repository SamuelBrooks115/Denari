import { Hero } from "@/components/Hero";
import { SectionHeader } from "@/components/SectionHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { BarChart3, Building2 } from "lucide-react";

export default function IndustryOverview() {
  return (
    <div className="min-h-screen">
      <Hero title="Industry Overview" subtitle="Comprehensive industry analysis and screening tools" />

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto space-y-8">
            <SectionHeader
              title="Why Industry Analysis Matters"
              subtitle="Understanding industry dynamics is crucial for accurate valuation"
            />

            <p className="text-lg text-muted-foreground text-center">
              Denari provides comprehensive industry analysis tools that help you understand market dynamics, identify
              trends, and screen potential investment opportunities. Our platform aggregates data from multiple sources
              to give you a complete picture of any industry.
            </p>

            <div className="grid md:grid-cols-2 gap-6 mt-12">
              <Card className="shadow-soft">
                <CardContent className="p-6">
                  <div className="aspect-video bg-gradient-card rounded-lg flex items-center justify-center mb-4">
                    <BarChart3 className="h-16 w-16 text-white opacity-50" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Example Screenshot 1</h3>
                  <p className="text-muted-foreground">
                    Industry performance metrics and comparative analysis across sectors
                  </p>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardContent className="p-6">
                  <div className="aspect-video bg-gradient-card rounded-lg flex items-center justify-center mb-4">
                    <Building2 className="h-16 w-16 text-white opacity-50" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Example Screenshot 2</h3>
                  <p className="text-muted-foreground">Company screening with customizable filters and criteria</p>
                </CardContent>
              </Card>
            </div>

            <div className="bg-muted/50 rounded-2xl p-8 mt-12">
              <h3 className="text-2xl font-bold mb-4 text-center">How Denari Helps Screen Companies</h3>
              <p className="text-muted-foreground text-center mb-6">
                Our intelligent screening tools allow you to quickly identify companies that meet your investment
                criteria. Filter by financial metrics, growth rates, valuation multiples, and more. Denari's
                industry-specific templates ensure you're using the right metrics for each sector.
              </p>
              <div className="text-center">
                <Link to="/app/projects/new">
                  <Button size="lg" className="bg-primary hover:bg-primary/90">
                    Start Screening Companies
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
