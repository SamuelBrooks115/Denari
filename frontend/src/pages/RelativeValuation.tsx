import { Hero } from "@/components/Hero";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart2, PieChart } from "lucide-react";

export default function RelativeValuation() {
  return (
    <div className="min-h-screen">
      <Hero title="Relative Valuation" subtitle="Compare companies using industry-standard multiples" />

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto">
            <div className="grid md:grid-cols-2 gap-8 mb-12">
              <Card className="shadow-soft">
                <CardContent className="p-6">
                  <div className="aspect-video bg-gradient-card rounded-lg flex items-center justify-center mb-4">
                    <BarChart2 className="h-16 w-16 text-white opacity-50" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Photo of Output 1</h3>
                  <p className="text-muted-foreground">
                    Comprehensive comparable company analysis with automated peer selection
                  </p>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardContent className="p-6">
                  <div className="aspect-video bg-gradient-card rounded-lg flex items-center justify-center mb-4">
                    <PieChart className="h-16 w-16 text-white opacity-50" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Photo of Output 2</h3>
                  <p className="text-muted-foreground">
                    Visual representations of valuation multiples with statistical analysis
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-8">
              <div className="bg-muted/50 rounded-2xl p-8">
                <h3 className="text-2xl font-bold mb-4">The Relative Valuation Method</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Relative valuation compares a company's valuation multiples to those of similar companies in the same
                  industry. This method is widely used by investment professionals because it provides market-based
                  context for valuations. Common multiples include P/E, EV/EBITDA, P/B, and EV/Sales.
                </p>
              </div>

              <div className="bg-muted/50 rounded-2xl p-8">
                <h3 className="text-2xl font-bold mb-4">Why It Is Important</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Relative valuation provides a reality check against absolute valuation methods like DCF. It helps
                  answer the question: "How does the market value similar companies?" This is crucial for understanding
                  whether a company is overvalued or undervalued relative to its peers. Our platform handles outliers intelligently and provides statistical measures to support
                  your conclusions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
