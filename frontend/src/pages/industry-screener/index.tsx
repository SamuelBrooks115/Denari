import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Filter } from "lucide-react";

export default function IndustryScreenerIndex() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto text-center">
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
              <Filter className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-4xl font-bold mb-4">Industry Screener</h1>
            <p className="text-xl text-muted-foreground">
              Filter companies by sector, industry, and market cap
            </p>
          </div>

          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Get Started</CardTitle>
              <CardDescription>
                Use our powerful screening tool to find companies that match your investment criteria
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => navigate("/industry-screener/search")}
                size="lg"
                className="w-full sm:w-auto"
              >
                Start Screening Companies
              </Button>
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Sector Filter</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Filter companies by industry sector such as Technology, Healthcare, or Financial Services
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Industry Filter</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Narrow down results by specific industry within each sector
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Market Cap Range</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Set minimum and maximum market capitalization to find companies in your target size range
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

