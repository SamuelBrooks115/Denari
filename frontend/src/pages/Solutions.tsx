import { Hero } from "@/components/Hero";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { Check, Users } from "lucide-react";
import { useState } from "react";

export default function Solutions() {
  const [employees, setEmployees] = useState("5");
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "quarterly">("quarterly");

  const features = [
    "Up to 10 employees",
    "Capped monthly usage",
    "By-seat pricing",
    "3-Statement Models",
    "DCF Analysis",
    "Relative Valuation",
    "Excel Export",
    "Email Support",
  ];

  const monthlyPrice = Number(employees) * 99;
  const quarterlyPrice = 499;
  const displayPrice = billingPeriod === "quarterly" ? quarterlyPrice : monthlyPrice;
  const displayPeriod = billingPeriod === "quarterly" ? "quarter" : "month";

  return (
    <div className="min-h-screen">
      <Hero title="Solutions" subtitle="Choose the plan that fits your needs" />

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto">
            <Card className="shadow-elevated border-2 border-primary/20">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Users className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle className="text-2xl">Denari Professional</CardTitle>
                </div>
                <p className="text-muted-foreground">Perfect for smaller offices and teams</p>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="employees">Number of Employees</Label>
                    <Input
                      id="employees"
                      type="number"
                      min="1"
                      max="10"
                      value={employees}
                      onChange={(e) => setEmployees(e.target.value)}
                      className="mt-1"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Maximum 10 people</p>
                  </div>

                  <div className="flex gap-2">
                    <Button 
                      variant={billingPeriod === "monthly" ? "default" : "outline"} 
                      size="sm" 
                      className="flex-1"
                      onClick={() => setBillingPeriod("monthly")}
                    >
                      Monthly
                    </Button>
                    <Button 
                      variant={billingPeriod === "quarterly" ? "default" : "outline"} 
                      size="sm" 
                      className="flex-1"
                      onClick={() => setBillingPeriod("quarterly")}
                    >
                      Quarterly
                    </Button>
                  </div>

                  <div className="bg-muted rounded-lg p-4">
                    <p className="text-2xl font-bold text-primary">
                      ${displayPrice.toLocaleString()}
                      <span className="text-sm font-normal text-muted-foreground">/{displayPeriod}</span>
                    </p>
                    {billingPeriod === "monthly" && (
                      <p className="text-xs text-muted-foreground mt-1">$99 per seat/month</p>
                    )}
                    {billingPeriod === "quarterly" && (
                      <p className="text-xs text-muted-foreground mt-1">$499 per quarter</p>
                    )}
                  </div>
                </div>

                <div className="space-y-3">
                  {features.map((feature) => (
                    <div key={feature} className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-success flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </div>
                  ))}
                </div>

                <Button className="w-full bg-primary hover:bg-primary/90">Get Started</Button>
              </CardContent>
            </Card>

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
