import { Lightbulb } from "lucide-react";

export default function Strategy() {
  return (
    <div className="min-h-screen">
      <div className="relative h-64 bg-gradient-hero overflow-hidden">
        <div className="absolute inset-0 bg-denari-1/50 backdrop-blur-sm" />
        <div className="relative h-full flex items-center justify-center">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-4 rounded-full bg-primary/20">
                <Lightbulb className="h-12 w-12 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-white">Our Strategy</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto">
          <div className="bg-muted/50 rounded-2xl p-8">
            <h2 className="text-2xl font-bold mb-6 text-denari-1">Strategy</h2>
            <div className="prose max-w-none">
              <p className="text-lg text-muted-foreground leading-relaxed mb-4">
                Our strategy centers on three core principles: listening to our users, maintaining the highest standards
                of accuracy, and continuously innovating to stay ahead of industry needs.
              </p>

              <p className="text-lg text-muted-foreground leading-relaxed mb-4">
                We invest heavily in understanding the workflows of investment professionals. Every feature request is
                evaluated against real-world use cases. We build tools that integrate seamlessly into existing
                processes rather than requiring users to adapt to new paradigms.
              </p>

              <p className="text-lg text-muted-foreground leading-relaxed mb-4">
                Accuracy is non-negotiable. We employ rigorous testing protocols and work with industry veterans to
                validate our models. Our platform is built on proven methodologies used by leading investment banks and
                private equity firms.
              </p>

              <p className="text-lg text-muted-foreground leading-relaxed">
                Innovation drives our roadmap. We're constantly exploring new ways to leverage technology to improve the
                valuation process. From intelligent defaults to automated peer selection, we're building features that
                make professionals more efficient without sacrificing control or transparency.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
