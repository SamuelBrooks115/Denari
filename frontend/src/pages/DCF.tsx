import { Hero } from "@/components/Hero";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/SectionHeader";
import { FileSpreadsheet, Layers } from "lucide-react";
import { Star } from "lucide-react";

export default function DCF() {
  const reviews = [
    {
      author: "Sarah Johnson, Portfolio Manager",
      text: "Denari's DCF module has completely transformed our valuation workflow. The ability to save and layer preferences has saved us countless hours.",
      rating: 5,
    },
    {
      author: "Michael Chen, Research Analyst",
      text: "The integration with 3-statement models is seamless. I can build a comprehensive model in a fraction of the time it used to take.",
      rating: 5,
    },
    {
      author: "Emily Rodriguez, Investment Banker",
      text: "Professional-grade output that I can confidently present to clients. The customization options are exactly what we need.",
      rating: 5,
    },
  ];

  return (
    <div className="min-h-screen">
      <Hero title="DCF Valuation" subtitle="Sophisticated discounted cash flow analysis" />

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto space-y-12">
            <SectionHeader
              title="Two Powerful Format Options"
              subtitle="Choose the DCF layout that works best for your needs"
            />

            <div className="grid md:grid-cols-2 gap-8">
              <Card className="shadow-soft">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <FileSpreadsheet className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle>Format Option 1</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="aspect-video bg-gradient-card rounded-lg flex items-center justify-center mb-4">
                    <FileSpreadsheet className="h-16 w-16 text-white opacity-50" />
                  </div>
                  <p className="text-muted-foreground">
                    Traditional vertical DCF layout with detailed assumptions and drivers clearly displayed. Ideal for
                    presentations and client reports.
                  </p>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Layers className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle>Format Option 2</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="aspect-video bg-gradient-card rounded-lg flex items-center justify-center mb-4">
                    <Layers className="h-16 w-16 text-white opacity-50" />
                  </div>
                  <p className="text-muted-foreground">
                    Horizontal compact layout optimized for detailed analysis. Perfect for working models and internal
                    analysis.
                  </p>
                </CardContent>
              </Card>
            </div>

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

            <div>
              <SectionHeader title="What Our Users Say" subtitle="Trusted by investment professionals worldwide" />
              <div className="grid md:grid-cols-3 gap-6 mt-8">
                {reviews.map((review, index) => (
                  <Card key={index} className="shadow-soft">
                    <CardContent className="p-6">
                      <div className="flex gap-1 mb-3">
                        {Array.from({ length: review.rating }).map((_, i) => (
                          <Star key={i} className="h-4 w-4 fill-accent text-accent" />
                        ))}
                      </div>
                      <p className="text-sm text-muted-foreground mb-4 italic">"{review.text}"</p>
                      <p className="text-sm font-semibold">{review.author}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
