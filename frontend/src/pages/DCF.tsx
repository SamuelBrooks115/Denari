import { Hero } from "@/components/Hero";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileSpreadsheet } from "lucide-react";
import { useEffect } from "react";

export default function DCF() {
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);
  return (
    <div className="min-h-screen">
      <Hero title="DCF Valuation" subtitle="Sophisticated discounted cash flow analysis" />

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto space-y-12">
            {/* Single Clean Output Example */}
            <Card className="shadow-soft">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <FileSpreadsheet className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>DCF Analysis Output</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="aspect-video bg-gradient-card rounded-lg overflow-hidden mb-4">
                  <img 
                    src="/photos/DCF_EX.png" 
                    alt="DCF Analysis Excel Output" 
                    className="w-full h-full object-contain"
                  />
                </div>
                <p className="text-muted-foreground">
                  Comprehensive DCF analysis with detailed assumptions and drivers clearly displayed. 
                  Ideal for presentations and client reports.
                </p>
              </CardContent>
            </Card>

            <div className="bg-muted/50 rounded-2xl p-8">
              <h3 className="text-2xl font-bold mb-4 text-center">Intelligent Preferences</h3>
              <p className="text-muted-foreground text-center leading-relaxed">
                Denari's DCF module uses pre-saved preferences that intelligently layer onto your 3-statement
                assumptions. This means you can maintain consistent methodologies across projects while still having the
                flexibility to adjust individual models. Change your discount rate assumptions globally, and all your
                models update automatically. Override specific assumptions when needed without losing your baseline
                preferences.
              </p>
            </div>

            {/* Optional: AIM Reviews Section (placeholder) */}
            <div>
              <h3 className="text-2xl font-bold mb-4 text-center">AIM Reviews</h3>
              <p className="text-muted-foreground text-center">
                AI-powered reviews coming soon
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
