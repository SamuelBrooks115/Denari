import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Search, ArrowRight, ArrowLeft, CheckCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

type WizardStep =
  | "search"
  | "details"
  | "model-type"
  | "frequency"
  | "periods"
  | "income-statement"
  | "revenue-config"
  | "review";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function NewProjectWizard() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<WizardStep>("search");
  const [isSearching, setIsSearching] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [wizardData, setWizardData] = useState({
    ticker: "",
    companyName: "",
    modelTypes: [] as string[],
    frequency: "annual", // Default to annual
    historicalPeriods: "5", // Default values
    forecastPeriods: "5",
    revenueStepRate: "",
    revenueStages: "1",
  });

  const steps: WizardStep[] = [
    "search",
    "details",
    "model-type",
    "frequency",
    "periods",
    "income-statement",
    "revenue-config",
    "review",
  ];

  const currentStepIndex = steps.indexOf(currentStep);
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  const handleNext = () => {
    // Validate current step before advancing
    if (currentStep === "search" && !wizardData.ticker.trim()) {
      toast.error("Please search for a company first");
      return;
    }
    if (currentStep === "frequency" && !wizardData.frequency) {
      toast.error("Please select a frequency");
      return;
    }
    if (currentStep === "periods") {
      if (!wizardData.historicalPeriods || parseInt(wizardData.historicalPeriods) < 1) {
        toast.error("Please enter a valid number of historical periods (minimum 1)");
        return;
      }
      if (!wizardData.forecastPeriods || parseInt(wizardData.forecastPeriods) < 1) {
        toast.error("Please enter a valid number of forecast periods (minimum 1)");
        return;
      }
    }
    
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < steps.length) {
      setCurrentStep(steps[nextIndex]);
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex]);
    }
  };

  const handleSearch = async () => {
    if (!wizardData.ticker.trim()) {
      toast.error("Please enter a ticker symbol");
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/models/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ticker: wizardData.ticker.toUpperCase() }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to search company");
      }

      const data = await response.json();
      
      if (data.found) {
        setWizardData({
          ...wizardData,
          ticker: data.ticker,
          companyName: data.name || data.ticker,
        });
        toast.success("Company found!", {
          description: data.name || data.ticker,
        });
        // Auto-advance to next step
        handleNext();
      } else {
        const errorMsg = data.error || `No data found for ticker: ${wizardData.ticker}`;
        toast.error("Company not found", {
          description: errorMsg,
        });
      }
    } catch (error) {
      toast.error("Search failed", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleFinish = async () => {
    // Validate required fields
    if (!wizardData.ticker.trim()) {
      toast.error("Ticker is required");
      return;
    }
    if (!wizardData.frequency) {
      toast.error("Please select a frequency");
      return;
    }
    if (!wizardData.historicalPeriods || parseInt(wizardData.historicalPeriods) < 1) {
      toast.error("Please specify historical periods");
      return;
    }
    if (!wizardData.forecastPeriods || parseInt(wizardData.forecastPeriods) < 1) {
      toast.error("Please specify forecast periods");
      return;
    }

    setIsGenerating(true);
    try {
      // Build assumptions from wizard data
      const assumptions: Record<string, any> = {
        revenue_growth: wizardData.revenueStepRate 
          ? parseFloat(wizardData.revenueStepRate) / 100 
          : 0.05, // Default 5%
        operating_margin_target: 0.15, // Default 15%
        tax_rate: 0.21, // Default 21%
        capex_as_pct_revenue: 0.05, // Default 5%
        depreciation_as_pct_revenue: 0.03, // Default 3%
        wacc: 0.10, // Default 10%
        terminal_growth_rate: 0.025, // Default 2.5%
      };

      const response = await fetch(`${API_BASE_URL}/api/v1/models/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticker: wizardData.ticker.toUpperCase(),
          frequency: wizardData.frequency,
          historical_periods: parseInt(wizardData.historicalPeriods),
          forecast_periods: parseInt(wizardData.forecastPeriods),
          assumptions,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate model");
      }

      const modelData = await response.json();
      
      // Store model data in sessionStorage and redirect to model page
      sessionStorage.setItem("current_model", JSON.stringify(modelData));
      
      toast.success("Model generated successfully!", {
        description: "Redirecting to model page...",
      });
      
      // Redirect to model page
      navigate("/app/model");
    } catch (error) {
      toast.error("Model generation failed", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-4">New Project Wizard</h1>
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-muted-foreground text-right">
                Step {currentStepIndex + 1} of {steps.length}
              </p>
            </div>
          </div>

          <Card className="shadow-elevated">
            <CardContent className="p-8">
              {currentStep === "search" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Search S&P 500 Company</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="bg-muted/50 p-4 rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        Enter a ticker symbol for an S&P 500 company (e.g., AAPL, MSFT, GOOGL)
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="search">Ticker Symbol</Label>
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          handleSearch();
                        }}
                        className="flex gap-2"
                      >
                        <Input
                          id="search"
                          placeholder="e.g., AAPL"
                          value={wizardData.ticker}
                          onChange={(e) => setWizardData({ ...wizardData, ticker: e.target.value.toUpperCase() })}
                          disabled={isSearching}
                          autoFocus
                        />
                        <Button 
                          type="submit"
                          variant="outline" 
                          size="icon"
                          disabled={isSearching || !wizardData.ticker.trim()}
                        >
                          {isSearching ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Search className="h-4 w-4" />
                          )}
                        </Button>
                      </form>
                    </div>
                    {wizardData.companyName && (
                      <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
                        <p className="text-sm font-medium">Selected: {wizardData.companyName}</p>
                        <p className="text-xs text-muted-foreground">Ticker: {wizardData.ticker}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {currentStep === "details" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Company Details</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="bg-muted/50 p-4 rounded-lg space-y-2">
                      <p className="font-medium">{wizardData.companyName || "Company Name"}</p>
                      <p className="text-sm text-muted-foreground">Ticker: {wizardData.ticker}</p>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Company information has been retrieved from EDGAR. You can proceed to the next step.
                    </p>
                  </div>
                </div>
              )}

              {currentStep === "model-type" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Model Type</CardTitle>
                  </CardHeader>
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      MVP includes 3-Statement Model, DCF Valuation, and Relative Valuation (Comps).
                      All models will be generated automatically.
                    </p>
                  </div>
                  <div className="grid md:grid-cols-3 gap-4">
                    {["3-Statement Model", "DCF Valuation", "Relative Valuation"].map((type) => (
                      <Card
                        key={type}
                        className="border-primary bg-primary/5"
                      >
                        <CardContent className="p-6 text-center">
                          <p className="font-medium">{type}</p>
                          <Badge variant="secondary" className="mt-2">
                            Included
                          </Badge>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {currentStep === "frequency" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>3-Statement Modeling Setup</CardTitle>
                  </CardHeader>
                  <div className="space-y-3">
                    <Label>Select Frequency</Label>
                    <RadioGroup
                      value={wizardData.frequency}
                      onValueChange={(value) => setWizardData({ ...wizardData, frequency: value })}
                    >
                      <div className="grid md:grid-cols-2 gap-4">
                        <Card
                          className={`cursor-pointer ${
                            wizardData.frequency === "quarterly" ? "border-primary bg-primary/5" : ""
                          }`}
                        >
                          <CardContent className="p-6">
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="quarterly" id="quarterly" />
                              <Label htmlFor="quarterly" className="cursor-pointer font-medium">
                                Quarterly
                              </Label>
                            </div>
                          </CardContent>
                        </Card>
                        <Card
                          className={`cursor-pointer ${
                            wizardData.frequency === "annual" ? "border-primary bg-primary/5" : ""
                          }`}
                        >
                          <CardContent className="p-6">
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="annual" id="annual" />
                              <Label htmlFor="annual" className="cursor-pointer font-medium">
                                Annual
                              </Label>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    </RadioGroup>
                  </div>
                </div>
              )}

              {currentStep === "periods" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Historical & Forecast Periods</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="historical">How many years of historical data?</Label>
                      <Input
                        id="historical"
                        type="number"
                        min="1"
                        max="10"
                        value={wizardData.historicalPeriods}
                        onChange={(e) => {
                          const val = e.target.value;
                          if (val === "" || (parseInt(val) >= 1 && parseInt(val) <= 10)) {
                            setWizardData({ ...wizardData, historicalPeriods: val });
                          }
                        }}
                      />
                      <p className="text-xs text-muted-foreground">Recommended: 3-5 years</p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="forecast">How many years to forecast?</Label>
                      <Input
                        id="forecast"
                        type="number"
                        min="1"
                        max="10"
                        value={wizardData.forecastPeriods}
                        onChange={(e) => {
                          const val = e.target.value;
                          if (val === "" || (parseInt(val) >= 1 && parseInt(val) <= 10)) {
                            setWizardData({ ...wizardData, forecastPeriods: val });
                          }
                        }}
                      />
                      <p className="text-xs text-muted-foreground">Recommended: 5 years</p>
                    </div>
                  </div>
                </div>
              )}

              {currentStep === "income-statement" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Income Statement Configuration</CardTitle>
                  </CardHeader>
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      The model will automatically extract and use historical financial data from EDGAR filings.
                      All line items will be modeled based on historical trends and your assumptions.
                    </p>
                  </div>
                  <div className="space-y-2">
                    {["Revenue", "Cost of Goods Sold", "Operating Expenses", "Operating Income", "Net Income"].map((item) => (
                      <Card key={item} className="border-l-4 border-l-primary">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{item}</span>
                            <Badge variant="secondary">
                              Auto-extracted
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {currentStep === "revenue-config" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Revenue Growth Assumptions</CardTitle>
                  </CardHeader>

                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      Specify the annual revenue growth rate for projections. If left blank, a default of 5% will be used.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="stepRate">Annual Revenue Growth Rate (%)</Label>
                      <Input
                        id="stepRate"
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                        placeholder="e.g., 15"
                        value={wizardData.revenueStepRate}
                        onChange={(e) => {
                          const val = e.target.value;
                          if (val === "" || (parseFloat(val) >= 0 && parseFloat(val) <= 100)) {
                            setWizardData({ ...wizardData, revenueStepRate: val });
                          }
                        }}
                      />
                      <p className="text-xs text-muted-foreground">
                        {wizardData.revenueStepRate 
                          ? `Using ${wizardData.revenueStepRate}% annual growth` 
                          : "Will use default 5% annual growth if not specified"}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {currentStep === "review" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Review Configuration</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="bg-muted/50 p-4 rounded-lg space-y-2">
                      <p className="font-medium">Company: {wizardData.companyName || "Not specified"}</p>
                      <p className="text-sm text-muted-foreground">Ticker: {wizardData.ticker || "Not specified"}</p>
                      <p className="text-sm text-muted-foreground">
                        Frequency: {wizardData.frequency || "Not specified"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Historical Periods: {wizardData.historicalPeriods || "Not specified"} {wizardData.frequency === "annual" ? "years" : "quarters"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Forecast Periods: {wizardData.forecastPeriods || "Not specified"} {wizardData.frequency === "annual" ? "years" : "quarters"}
                      </p>
                      {wizardData.revenueStepRate && (
                        <p className="text-sm text-muted-foreground">
                          Revenue Growth: {wizardData.revenueStepRate}% annually
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      Ready to generate model
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-between mt-8 pt-6 border-t">
                <Button onClick={handleBack} variant="outline" disabled={currentStepIndex === 0}>
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>

                {currentStepIndex === steps.length - 1 ? (
                  <Button 
                    onClick={handleFinish} 
                    className="bg-primary hover:bg-primary/90" 
                    disabled={isGenerating}
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      "Generate Model"
                    )}
                  </Button>
                ) : (
                  <Button onClick={handleNext} className="bg-primary hover:bg-primary/90">
                    Next
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

