import { Badge } from "@/components/ui/badge";
import { Focus as FocusIcon } from "lucide-react";

export default function Focus() {
  const keywords = ["Innovate", "Automate", "Improve"];

  return (
    <div className="min-h-screen">
      <div className="relative h-64 bg-gradient-hero overflow-hidden">
        <div className="absolute inset-0 bg-denari-1/50 backdrop-blur-sm" />
        <div className="relative h-full flex items-center justify-center">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-4 rounded-full bg-primary/20">
                <FocusIcon className="h-12 w-12 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-white">Our Focus</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="bg-muted/50 rounded-2xl p-8">
            <h2 className="text-2xl font-bold mb-6 text-denari-1">Who We Focus On & Why</h2>
            <div className="prose max-w-none">
              <p className="text-lg text-muted-foreground leading-relaxed mb-4">
                We focus on investment professionals who demand precision and efficiency. Our primary users include
                equity research analysts, portfolio managers, investment bankers, and private equity associates—professionals
                who build complex financial models as part of their daily workflow.
              </p>

              <p className="text-lg text-muted-foreground leading-relaxed mb-4">
                These professionals face unique challenges: tight deadlines, high accuracy requirements, and the need to
                maintain consistency across multiple models. They need tools that enhance their expertise rather than
                replace it.
              </p>

              <p className="text-lg text-muted-foreground leading-relaxed">
                We chose this focus because we believe that by serving the most demanding users, we create a product
                that benefits everyone. The rigorous standards required by institutional investors naturally result in a
                platform that is robust, reliable, and feature-rich.
              </p>
            </div>
          </div>

          <div className="bg-gradient-card rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4 text-center">How We Drive Progress</h3>
            <div className="flex flex-wrap gap-3 mb-4 justify-center">
              {keywords.map((keyword) => (
                <Badge key={keyword} variant="secondary" className="text-base px-4 py-2 bg-white/20 text-white">
                  {keyword}
                </Badge>
              ))}
            </div>
            <p className="text-denari-4 leading-relaxed">
              We constantly innovate to find better solutions, automate repetitive tasks to save time, and improve every
              aspect of the modeling experience to deliver exceptional results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
