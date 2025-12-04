import { Hero } from "@/components/Hero";
import { Carousel } from "@/components/Carousel";
import { VideoPlayer } from "@/components/VideoPlayer";
import { SectionHeader } from "@/components/SectionHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link, useNavigate } from "react-router-dom";
import { FileSpreadsheet, TrendingUp, Calculator, Briefcase } from "lucide-react";

export default function Landing() {
  const navigate = useNavigate();

  const handleQuickLinkClick = (href: string, e: React.MouseEvent) => {
    e.preventDefault();
    // Scroll to top first
    window.scrollTo({ top: 0, behavior: 'smooth' });
    // Then navigate after a brief delay to ensure scroll starts
    setTimeout(() => {
      navigate(href);
    }, 100);
  };

  const carouselItems = [
    <Card key={1} className="shadow-soft">
      <CardHeader>
        <CardTitle>3 Statement Model</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="aspect-video bg-gradient-card rounded-lg overflow-hidden">
          <img 
            src="/photos/3Statement_EX.png" 
            alt="3 Statement Model Excel Output" 
            className="w-full h-full object-contain"
          />
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          Comprehensive 3-statement model with detailed assumptions and drivers
        </p>
      </CardContent>
    </Card>,
    <Card key={2} className="shadow-soft">
      <CardHeader>
        <CardTitle>DCF Valuation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="aspect-video bg-gradient-card rounded-lg overflow-hidden">
          <img 
            src="/photos/DCF_EX.png" 
            alt="DCF Valuation Excel Output" 
            className="w-full h-full object-contain"
          />
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          DCF valuation with sensitivity analysis and multiple scenarios
        </p>
      </CardContent>
    </Card>,
    <Card key={3} className="shadow-soft">
      <CardHeader>
        <CardTitle>Relative Valuation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="aspect-video bg-gradient-card rounded-lg overflow-hidden">
          <img 
            src="/photos/RC_EX.png" 
            alt="Relative Valuation Excel Output" 
            className="w-full h-full object-contain"
          />
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          Relative valuation comparables with automatic peer selection
        </p>
      </CardContent>
    </Card>,
  ];

  const quickLinks = [
    {
      title: "3 Statement Model",
      description: "Build comprehensive financial models with integrated statements",
      icon: FileSpreadsheet,
      href: "/three-statement",
    },
    {
      title: "Relative Valuation",
      description: "Compare companies using industry-standard multiples",
      icon: TrendingUp,
      href: "/relative-valuation",
    },
    {
      title: "DCF Analysis",
      description: "Perform detailed discounted cash flow valuations",
      icon: Calculator,
      href: "/dcf",
    },
    {
      title: "Solutions",
      description: "Explore our pricing plans and enterprise options",
      icon: Briefcase,
      href: "/solutions",
    },
  ];

  return (
    <div className="min-h-screen">
      <Hero
        title="DENARI"
        subtitle="Start Investing Using Denari Today"
        size="large"
        logo="/Logos/White%20Denari.png"
      >
        <Link to="/login">
          <Button size="lg" className="bg-primary hover:bg-primary/90 text-lg px-8">
            Get Started
          </Button>
        </Link>
      </Hero>

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <SectionHeader
            title="About Denari"
            subtitle="Professional-grade financial modeling and valuation tools built for investment professionals"
          />
          <div className="mt-8 max-w-3xl mx-auto">
            <p className="text-center text-lg text-muted-foreground">
              Denari streamlines the valuation process by automating complex financial models, allowing you to focus on
              analysis and decision-making. Our platform combines the power of traditional Excel modeling with modern
              automation and intelligent defaults.
            </p>
          </div>
        </div>
      </section>

      <section className="py-16 bg-muted/30">
        <div className="container mx-auto px-4">
          <SectionHeader title="Excel Outputs" subtitle="Professional-grade models exported directly to Excel" />
          <div className="mt-12 max-w-4xl mx-auto">
            <Carousel items={carouselItems} />
          </div>
        </div>
      </section>

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <SectionHeader title="See Denari in Action" subtitle="Watch how easy it is to build professional models" />
          <div className="mt-12 max-w-4xl mx-auto">
            <VideoPlayer />
          </div>
        </div>
      </section>

      <section className="py-16 bg-muted/30">
        <div className="container mx-auto px-4">
          <SectionHeader title="Quick Links" subtitle="Explore our powerful modeling capabilities" />
          <div className="mt-12 grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {quickLinks.map((link) => (
              <div
                key={link.href}
                onClick={(e) => handleQuickLinkClick(link.href, e)}
                className="cursor-pointer"
              >
                <Card className="h-full shadow-soft hover:shadow-elevated transition-all hover:scale-[1.02]">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <link.icon className="h-6 w-6 text-primary" />
                      </div>
                      <CardTitle>{link.title}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">{link.description}</p>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-denari-1">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Ready to Get Started?</h2>
          <p className="text-denari-4 mb-8 max-w-2xl mx-auto">
            Join investment professionals who trust Denari for their valuation needs
          </p>
          <Link to="/login">
            <Button size="lg" className="bg-primary hover:bg-primary/90">
              Start Your First Project
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
