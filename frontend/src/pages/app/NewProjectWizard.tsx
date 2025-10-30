import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Search, ArrowRight, ArrowLeft, CheckCircle } from "lucide-react";
import { toast } from "sonner";

type WizardStep =
  | "search"
  | "details"
  | "model-type"
  | "frequency"
  | "periods"
  | "income-statement"
  | "revenue-config"
  | "review";

export default function NewProjectWizard() {
  const [currentStep, setCurrentStep] = useState<WizardStep>("search");
  const [wizardData, setWizardData] = useState({
    ticker: "",
    companyName: "",
    modelTypes: [] as string[],
    frequency: "",
    historicalPeriods: "",
    forecastPeriods: "",
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

  const handleFinish = () => {
    toast.error("Backend not connected", {
      description: "Model generation requires backend integration",
    });
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
                    <CardTitle>Search Ticker or Company Name</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="search">Company Search</Label>
                      <div className="flex gap-2">
                        <Input
                          id="search"
                          placeholder="e.g., AAPL or Apple Inc."
                          value={wizardData.ticker}
                          onChange={(e) => setWizardData({ ...wizardData, ticker: e.target.value })}
                        />
                        <Button variant="outline" size="icon">
                          <Search className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {currentStep === "details" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Company Details</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="companyName">Company Name</Label>
                      <Input
                        id="companyName"
                        value={wizardData.companyName}
                        onChange={(e) => setWizardData({ ...wizardData, companyName: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="ticker">Ticker</Label>
                      <Input
                        id="ticker"
                        value={wizardData.ticker}
                        onChange={(e) => setWizardData({ ...wizardData, ticker: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
              )}

              {currentStep === "model-type" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>I would like to model...</CardTitle>
                  </CardHeader>
                  <div className="grid md:grid-cols-3 gap-4">
                    {["Company Bio", "Key Metrics / Ratios", "Industry Analysis"].map((type) => (
                      <Card
                        key={type}
                        className={`cursor-pointer transition-all hover:scale-105 ${
                          wizardData.modelTypes.includes(type) ? "border-primary bg-primary/5" : ""
                        }`}
                        onClick={() => {
                          const types = wizardData.modelTypes.includes(type)
                            ? wizardData.modelTypes.filter((t) => t !== type)
                            : [...wizardData.modelTypes, type];
                          setWizardData({ ...wizardData, modelTypes: types });
                        }}
                      >
                        <CardContent className="p-6 text-center">
                          <p className="font-medium">{type}</p>
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
                      <Label htmlFor="historical">How many historical periods?</Label>
                      <Input
                        id="historical"
                        type="number"
                        min="1"
                        value={wizardData.historicalPeriods}
                        onChange={(e) => setWizardData({ ...wizardData, historicalPeriods: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="forecast">How many forecast periods?</Label>
                      <Input
                        id="forecast"
                        type="number"
                        min="1"
                        value={wizardData.forecastPeriods}
                        onChange={(e) => setWizardData({ ...wizardData, forecastPeriods: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
              )}

              {currentStep === "income-statement" && (
                <div className="space-y-6">
                  <CardHeader className="p-0">
                    <CardTitle>Income Statement - Line Items</CardTitle>
                  </CardHeader>
                  <p className="text-sm text-muted-foreground">
                    Select line items to include. Items not selected will be modeled as straight-line % of revenue.
                  </p>
                  <div className="space-y-2">
                    {["Revenue", "Gross Margin", "Operating Margin", "EBITDA Margin", "Tax Rate"].map((item) => (
                      <Card key={item} className="border-l-4 border-l-primary">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{item}</span>
                            <Badge variant="secondary">Required</Badge>
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
                    <CardTitle>Revenue Configuration</CardTitle>
                  </CardHeader>

                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      Choose how to configure revenue growth assumptions
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="stepRate">Step Rate (%)</Label>
                      <Input
                        id="stepRate"
                        type="number"
                        placeholder="e.g., 15"
                        value={wizardData.revenueStepRate}
                        onChange={(e) => setWizardData({ ...wizardData, revenueStepRate: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground">Annual growth rate assumption</p>
                    </div>

                    <div className="space-y-2">
                      <Label>Advanced: Staged Growth</Label>
                      <RadioGroup
                        value={wizardData.revenueStages}
                        onValueChange={(value) => setWizardData({ ...wizardData, revenueStages: value })}
                      >
                        <div className="flex gap-4">
                          {["1", "2", "3"].map((num) => (
                            <div key={num} className="flex items-center space-x-2">
                              <RadioGroupItem value={num} id={`stages-${num}`} />
                              <Label htmlFor={`stages-${num}`}>{num} Stage{num !== "1" && "s"}</Label>
                            </div>
                          ))}
                        </div>
                      </RadioGroup>
                    </div>

                    {Number(wizardData.revenueStages) > 1 && (
                      <div className="space-y-3 p-4 bg-muted/30 rounded-lg">
                        {Array.from({ length: Number(wizardData.revenueStages) }).map((_, i) => (
                          <div key={i} className="space-y-2">
                            <Label>Stage {i + 1} Step Rate (%)</Label>
                            <Input type="number" placeholder={`Stage ${i + 1} growth rate`} />
                          </div>
                        ))}
                      </div>
                    )}
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
                        Historical Periods: {wizardData.historicalPeriods || "Not specified"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Forecast Periods: {wizardData.forecastPeriods || "Not specified"}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <CheckCircle className="h-4 w-4 text-success" />
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
                  <Button onClick={handleFinish} className="bg-primary hover:bg-primary/90" disabled>
                    Generate Model
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
