import { Badge } from "@/components/ui/badge";
import { Target } from "lucide-react";

export default function Mission() {
  const keywords = ["Innovation", "Accuracy", "Efficiency"];

  return (
    <div className="min-h-screen">
      <div className="relative h-64 bg-gradient-hero overflow-hidden">
        <div className="absolute inset-0 bg-denari-1/50 backdrop-blur-sm" />
        <div className="relative h-full flex items-center justify-center">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-4 rounded-full bg-primary/20">
                <Target className="h-12 w-12 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-white">Our Mission</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="bg-muted/50 rounded-2xl p-8 border-l-4 border-primary">
            <p className="text-xl font-medium text-denari-1 italic">
              "To democratize professional-grade financial modeling, making sophisticated valuation tools accessible to
              investment professionals of all levels."
            </p>
          </div>

          <div className="prose max-w-none">
            <p className="text-lg text-muted-foreground leading-relaxed">
              At Denari, we believe that accurate valuation should not be limited by time constraints or technical
              barriers. Our mission is to empower investment professionals with tools that combine the rigor of
              traditional financial modeling with the efficiency of modern automation.
            </p>

            <p className="text-lg text-muted-foreground leading-relaxed mt-4">
              We're building a platform that respects the expertise of financial professionals while eliminating the
              tedious, repetitive aspects of model building. Every feature we develop is guided by real-world feedback
              from analysts, portfolio managers, and investment bankers who use our platform daily.
            </p>

            <p className="text-lg text-muted-foreground leading-relaxed mt-4">
              Through continuous innovation and a commitment to accuracy, we're creating the future of financial
              analysis—one where professionals can focus on insights rather than spreadsheet mechanics.
            </p>
          </div>

          <div className="bg-gradient-card rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Our Core Values</h3>
            <div className="flex flex-wrap gap-3">
              {keywords.map((keyword) => (
                <Badge key={keyword} variant="secondary" className="text-base px-4 py-2 bg-white/20 text-white">
                  {keyword}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
