import { Hero } from "@/components/Hero";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { Check, Users, Crown } from "lucide-react";
import { useState } from "react";

export default function Solutions() {
  const [romaEmployees, setRomaEmployees] = useState("5");
  const [venusUsers, setVenusUsers] = useState("1");

  const romaFeatures = [
    "Up to 10 employees",
    "Capped monthly usage",
    "By-seat pricing",
    "3-Statement Models",
    "DCF Analysis",
    "Relative Valuation",
    "Excel Export",
    "Email Support",
  ];

  const venusFeatures = [
    "Unlimited usage",
    "Advanced analytics",
    "Priority support",
    "All Roma features",
    "Custom templates",
    "API access",
    "Dedicated account manager",
    "Training sessions",
  ];

  return (
    <div className="min-h-screen">
      <Hero title="Solutions" subtitle="Choose the plan that fits your needs" />

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-2 gap-8">
              <Card className="shadow-elevated border-2 border-primary/20">
                <CardHeader>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Users className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">Roma</CardTitle>
                  </div>
                  <p className="text-muted-foreground">Perfect for smaller offices and teams</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="roma-employees">Number of Employees</Label>
                      <Input
                        id="roma-employees"
                        type="number"
                        min="1"
                        max="10"
                        value={romaEmployees}
                        onChange={(e) => setRomaEmployees(e.target.value)}
                        className="mt-1"
                      />
                      <p className="text-xs text-muted-foreground mt-1">Maximum 10 people</p>
                    </div>

                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" className="flex-1">
                        Monthly
                      </Button>
                      <Button variant="outline" size="sm" className="flex-1">
                        Annual
                        <Badge variant="secondary" className="ml-2 bg-success text-success-foreground">
                          Save 20%
                        </Badge>
                      </Button>
                    </div>

                    <div className="bg-muted rounded-lg p-4">
                      <p className="text-2xl font-bold text-primary">
                        ${Number(romaEmployees) * 99}
                        <span className="text-sm font-normal text-muted-foreground">/month</span>
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">$99 per seat/month</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {romaFeatures.map((feature) => (
                      <div key={feature} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-success flex-shrink-0" />
                        <span className="text-sm">{feature}</span>
                      </div>
                    ))}
                  </div>

                  <Button className="w-full bg-primary hover:bg-primary/90">Get Started with Roma</Button>
                </CardContent>
              </Card>

              <Card className="shadow-elevated border-2 border-accent/30 relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-accent text-accent-foreground px-4 py-1 text-xs font-semibold">
                  PREMIUM
                </div>
                <CardHeader>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-accent/10">
                      <Crown className="h-6 w-6 text-accent" />
                    </div>
                    <CardTitle className="text-2xl">Venus</CardTitle>
                  </div>
                  <p className="text-muted-foreground">Unlimited power for professionals and individuals</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="venus-users">Number of Users</Label>
                      <Input
                        id="venus-users"
                        type="number"
                        min="1"
                        value={venusUsers}
                        onChange={(e) => setVenusUsers(e.target.value)}
                        className="mt-1"
                      />
                    </div>

                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" className="flex-1">
                        Monthly
                      </Button>
                      <Button variant="outline" size="sm" className="flex-1">
                        Annual
                        <Badge variant="secondary" className="ml-2 bg-success text-success-foreground">
                          Save 20%
                        </Badge>
                      </Button>
                    </div>

                    <div className="bg-muted rounded-lg p-4">
                      <p className="text-2xl font-bold text-accent">
                        ${Number(venusUsers) * 249}
                        <span className="text-sm font-normal text-muted-foreground">/month</span>
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">$249 per user/month</p>
                    </div>
                  </div>

                  <div className="bg-accent/10 rounded-lg p-4">
                    <p className="text-sm font-semibold mb-2">Why Choose Venus?</p>
                    <p className="text-sm text-muted-foreground">
                      Unlimited model building, advanced features, and dedicated support. Perfect for individuals who
                      demand the best or teams that need unrestricted access to all Denari capabilities.
                    </p>
                  </div>

                  <div className="space-y-3">
                    {venusFeatures.map((feature) => (
                      <div key={feature} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-success flex-shrink-0" />
                        <span className="text-sm">{feature}</span>
                      </div>
                    ))}
                  </div>

                  <Button className="w-full bg-accent hover:bg-accent/90 text-accent-foreground">
                    Get Started with Venus
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="mt-12 text-center bg-denari-1 rounded-2xl p-8 text-white">
              <h3 className="text-2xl font-bold mb-4">Need a Custom Solution?</h3>
              <p className="text-denari-4 mb-6">
                Contact us to discuss enterprise pricing and custom features for your organization
              </p>
              <Link to="/about/contact">
                <Button size="lg" variant="secondary" className="bg-white text-denari-1 hover:bg-white/90">
                  Contact Us About Pricing
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
