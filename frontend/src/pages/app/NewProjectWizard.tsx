import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { X } from "lucide-react";
import { toast } from "sonner";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Progress } from "@/components/ui/progress";
import { Search, ArrowRight, ArrowLeft, CheckCircle, Loader2 } from "lucide-react";

import { useNavigate } from "react-router-dom";

// Mock company data for autocomplete
const mockCompanies = [
  { name: "Apple Inc.", ticker: "AAPL" },
  { name: "Microsoft Corporation", ticker: "MSFT" },
  { name: "Amazon.com Inc.", ticker: "AMZN" },
  { name: "Alphabet Inc.", ticker: "GOOGL" },
  { name: "Meta Platforms Inc.", ticker: "META" },
  { name: "Tesla Inc.", ticker: "TSLA" },
  { name: "NVIDIA Corporation", ticker: "NVDA" },
  { name: "JPMorgan Chase & Co.", ticker: "JPM" },
];

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function NewProjectWizard() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCompany, setSelectedCompany] = useState<{ name: string; ticker: string } | null>(null);
  const [open, setOpen] = useState(false);
  
  const [currentStep, setCurrentStep] = useState<WizardStep>("search");
  const [isSearching, setIsSearching] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [wizardData, setWizardData] = useState({
    companyName: "",
    ticker: "",
    // Income Statement - 5 year forecast values
    revenueMethod: "step" as "stable" | "step" | "manual",
    revenueStableValue: "",
    revenueStepValue: "",
    revenueValues: ["", "", "", "", ""],
    grossMarginMethod: "step" as "stable" | "step" | "manual",
    grossMarginStableValue: "",
    grossMarginStepValue: "",
    grossMarginValues: ["", "", "", "", ""],
    operatingMarginMethod: "step" as "stable" | "step" | "manual",
    operatingMarginStableValue: "",
    operatingMarginStepValue: "",
    operatingMarginValues: ["", "", "", "", ""],
    taxRateMethod: "step" as "stable" | "step" | "manual",
    taxRateStableValue: "",
    taxRateStepValue: "",
    taxRateValues: ["", "", "", "", ""],
    // Balance Sheet
    depreciationMethod: "stable" as "stable" | "step" | "custom",
    depreciationStableValue: "",
    depreciationStepValue: "",
    depreciationValues: ["", "", "", "", ""],
    totalDebtMethod: "stable" as "stable" | "step" | "custom",
    totalDebtStableValue: "",
    totalDebtStepValue: "",
    totalDebtValues: ["", "", "", "", ""],
    inventoryMethod: "stable" as "stable" | "step" | "custom",
    inventoryStableValue: "",
    inventoryStepValue: "",
    inventoryValues: ["", "", "", "", ""],
    debtChangeMethod: "stable" as "stable" | "step" | "custom",
    debtChangeStableValue: "",
    debtChangeStepValue: "",
    debtChangeValues: ["", "", "", "", ""],
    // Cash Flow
    shareRepurchases: "",
    dividendPercentNI: "",
    deferredTaxMethod: "percent" as "percent",
    deferredTaxPercent: "",
    capexMethod: "revenue" as "revenue" | "depreciation",
    capexValue: "",
    changeInWCMethod: "stable" as "stable" | "step" | "manual",
    changeInWCStableValue: "",
    changeInWCStepValue: "",
    changeInWCValues: ["", "", "", "", ""],
    // DCF
    betaMethod: "manual" as "calculate" | "manual",
    beta: "",
    betaCalculated: "",
    betaReference: "",
    betaYears: "3" as "1" | "3" | "5",
    betaBenchmark: "S&P 500" as "S&P 500" | "NASDAQ" | "Russell 2000" | "Dow Jones",
    marketRiskPremium: "6.0",
    riskFreeRate: "2.5",
    terminalGrowthRate: "2.5",
    scenario: "bear" as "bear" | "bull",
    // Bear/Bull Scenario Assumptions
    bearRevenueMethod: "step" as "stable" | "step" | "manual",
    bearRevenueStableValue: "",
    bearRevenueStepValue: "",
    bearRevenueValues: ["", "", "", "", ""],
    bearGrossMarginMethod: "step" as "stable" | "step" | "manual",
    bearGrossMarginStableValue: "",
    bearGrossMarginStepValue: "",
    bearGrossMarginValues: ["", "", "", "", ""],
    bearOperatingMarginMethod: "step" as "stable" | "step" | "manual",
    bearOperatingMarginStableValue: "",
    bearOperatingMarginStepValue: "",
    bearOperatingMarginValues: ["", "", "", "", ""],
    bearTaxRateMethod: "step" as "stable" | "step" | "manual",
    bearTaxRateStableValue: "",
    bearTaxRateStepValue: "",
    bearTaxRateValues: ["", "", "", "", ""],
    bearCapexMethod: "revenue" as "revenue" | "depreciation",
    bearCapexValue: "",
    bearChangeInWCMethod: "stable" as "stable" | "step" | "manual",
    bearChangeInWCStableValue: "",
    bearChangeInWCStepValue: "",
    bearChangeInWCValues: ["", "", "", "", ""],
    bullRevenueMethod: "step" as "stable" | "step" | "manual",
    bullRevenueStableValue: "",
    bullRevenueStepValue: "",
    bullRevenueValues: ["", "", "", "", ""],
    bullGrossMarginMethod: "step" as "stable" | "step" | "manual",
    bullGrossMarginStableValue: "",
    bullGrossMarginStepValue: "",
    bullGrossMarginValues: ["", "", "", "", ""],
    bullOperatingMarginMethod: "step" as "stable" | "step" | "manual",
    bullOperatingMarginStableValue: "",
    bullOperatingMarginStepValue: "",
    bullOperatingMarginValues: ["", "", "", "", ""],
    bullTaxRateMethod: "step" as "stable" | "step" | "manual",
    bullTaxRateStableValue: "",
    bullTaxRateStepValue: "",
    bullTaxRateValues: ["", "", "", "", ""],
    bullCapexMethod: "revenue" as "revenue" | "depreciation",
    bullCapexValue: "",
    bullChangeInWCMethod: "stable" as "stable" | "step" | "manual",
    bullChangeInWCStableValue: "",
    bullChangeInWCStepValue: "",
    bullChangeInWCValues: ["", "", "", "", ""],
    // Relative Valuation
    competitors: [] as string[],
  });

  const filteredCompanies = mockCompanies.filter(
    (company) =>
      company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      company.ticker.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCompanySelect = (company: { name: string; ticker: string }) => {
    setSelectedCompany(company);
    setWizardData({ ...wizardData, companyName: company.name, ticker: company.ticker });
    setSearchQuery(company.name);
    setOpen(false);
  };

  const handleFinish = () => {
    if (!selectedCompany) {
      toast.error("Please select a company");
      return;
    }
    toast.success("Project created successfully!");
    navigate("/app/projects");
  };

  // Mock historical financials (last 3 years)
  const historicalFinancials = {
    income: [
      { 
        year: "2022", 
        revenue: 125000, 
        grossProfit: 62500, 
        operatingExpenses: 37500, 
        ebitda: 25000, 
        netIncome: 18750,
        taxRate: 25.0,
        depreciationPercentPPE: 10.0,
        totalDebt: 50000,
        inventory: 18000,
        capexPercentPPE: 8.0,
        capexPercentRevenue: 6.4,
        shareRepurchases: 5000,
        dividendPercentNI: 25.0,
        changeInWC: 2000
      },
      { 
        year: "2023", 
        revenue: 142000, 
        grossProfit: 72100, 
        operatingExpenses: 42600, 
        ebitda: 29500, 
        netIncome: 22130,
        taxRate: 25.0,
        depreciationPercentPPE: 10.0,
        totalDebt: 55000,
        inventory: 21000,
        capexPercentPPE: 8.5,
        capexPercentRevenue: 7.0,
        shareRepurchases: 6000,
        dividendPercentNI: 25.0,
        changeInWC: 3000
      },
      { 
        year: "2024", 
        revenue: 165000, 
        grossProfit: 85800, 
        operatingExpenses: 49500, 
        ebitda: 36300, 
        netIncome: 27225,
        taxRate: 25.0,
        depreciationPercentPPE: 10.0,
        totalDebt: 60000,
        inventory: 24000,
        capexPercentPPE: 9.0,
        capexPercentRevenue: 7.3,
        shareRepurchases: 7000,
        dividendPercentNI: 25.0,
        changeInWC: 4000
      },
    ],
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-4">Create New Project</h1>
          </div>

          <Card className="shadow-elevated">
            <CardContent className="p-8 space-y-8">
              {/* Company Search */}
              <div className="space-y-4">
                  <CardHeader className="p-0">
                  <CardTitle>Company Search</CardTitle>
                  </CardHeader>
                    <div className="space-y-2">
                  <Label htmlFor="search">Company Name or Ticker</Label>
                  <Popover open={open} onOpenChange={setOpen}>
                    <PopoverTrigger asChild>
                      <div className="w-full">
                        <Input
                          id="search"
                          placeholder="e.g., AAPL or Apple Inc."
                          value={searchQuery}
                          onChange={(e) => {
                            setSearchQuery(e.target.value);
                            setOpen(true);
                          }}
                          onFocus={() => setOpen(true)}
                        />
                      </div>
                    </PopoverTrigger>
                    <PopoverContent className="w-[400px] p-0" align="start">
                      <Command>
                        <CommandInput placeholder="Search companies..." />
                        <CommandList>
                          <CommandEmpty>No companies found.</CommandEmpty>
                          <CommandGroup>
                            {filteredCompanies.map((company) => (
                              <CommandItem
                                key={company.ticker}
                                value={`${company.name} ${company.ticker}`}
                                onSelect={() => handleCompanySelect(company)}
                              >
                                <div className="flex flex-col">
                                  <span className="font-medium">{company.name}</span>
                                  <span className="text-xs text-muted-foreground">{company.ticker}</span>
                    </div>
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                </div>
                
                {selectedCompany && (
                  <div className="p-4 bg-muted/50 rounded-lg border">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{selectedCompany.name}</p>
                        <p className="text-sm text-muted-foreground">Ticker: {selectedCompany.ticker}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedCompany(null);
                          setSearchQuery("");
                          setWizardData({ ...wizardData, companyName: "", ticker: "" });
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                  </div>
                </div>
              )}
              </div>

              <div className="border-t pt-6">
                {/* Historical Financials Display */}
                <div className="space-y-4 mb-8">
                  <h3 className="text-lg font-semibold">Last 3 Years of Financials</h3>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-denari-2/5">
                          <TableHead>Field</TableHead>
                          <TableHead className="text-right">{historicalFinancials.income[0]?.year}</TableHead>
                          <TableHead className="text-right">{historicalFinancials.income[1]?.year}</TableHead>
                          <TableHead className="text-right">{historicalFinancials.income[2]?.year}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow>
                          <TableCell className="font-medium">Revenue Growth</TableCell>
                          <TableCell className="text-right">-</TableCell>
                          <TableCell className="text-right">
                            {historicalFinancials.income[0] && historicalFinancials.income[1]
                              ? `${(((historicalFinancials.income[1].revenue - historicalFinancials.income[0].revenue) / historicalFinancials.income[0].revenue) * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            {historicalFinancials.income[1] && historicalFinancials.income[2]
                              ? `${(((historicalFinancials.income[2].revenue - historicalFinancials.income[1].revenue) / historicalFinancials.income[1].revenue) * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Gross Margin</TableCell>
                          <TableCell className="text-right">
                            {historicalFinancials.income[0]?.revenue
                              ? `${((historicalFinancials.income[0].grossProfit / historicalFinancials.income[0].revenue) * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            {historicalFinancials.income[1]?.revenue
                              ? `${((historicalFinancials.income[1].grossProfit / historicalFinancials.income[1].revenue) * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            {historicalFinancials.income[2]?.revenue
                              ? `${((historicalFinancials.income[2].grossProfit / historicalFinancials.income[2].revenue) * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Operating Margin</TableCell>
                          <TableCell className="text-right">
                            {historicalFinancials.income[0]?.revenue
                              ? `${(((historicalFinancials.income[0].revenue - historicalFinancials.income[0].operatingExpenses) / historicalFinancials.income[0].revenue) * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            {historicalFinancials.income[1]?.revenue
                              ? `${(((historicalFinancials.income[1].revenue - historicalFinancials.income[1].operatingExpenses) / historicalFinancials.income[1].revenue) * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            {historicalFinancials.income[2]?.revenue
                              ? `${(((historicalFinancials.income[2].revenue - historicalFinancials.income[2].operatingExpenses) / historicalFinancials.income[2].revenue) * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Tax Rate</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[0]?.taxRate?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[1]?.taxRate?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[2]?.taxRate?.toFixed(1) || '-'}%</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Depreciation as % of PPE</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[0]?.depreciationPercentPPE?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[1]?.depreciationPercentPPE?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[2]?.depreciationPercentPPE?.toFixed(1) || '-'}%</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Total Debt Amount</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[0]?.totalDebt || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[1]?.totalDebt || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[2]?.totalDebt || 0)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Inventory</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[0]?.inventory || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[1]?.inventory || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[2]?.inventory || 0)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">CAPEX % of PPE</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[0]?.capexPercentPPE?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[1]?.capexPercentPPE?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[2]?.capexPercentPPE?.toFixed(1) || '-'}%</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">CAPEX % of Revenue</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[0]?.capexPercentRevenue?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[1]?.capexPercentRevenue?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[2]?.capexPercentRevenue?.toFixed(1) || '-'}%</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Share Repurchases</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[0]?.shareRepurchases || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[1]?.shareRepurchases || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[2]?.shareRepurchases || 0)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">DIV as % of NI</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[0]?.dividendPercentNI?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[1]?.dividendPercentNI?.toFixed(1) || '-'}%</TableCell>
                          <TableCell className="text-right">{historicalFinancials.income[2]?.dividendPercentNI?.toFixed(1) || '-'}%</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Change in WC</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[0]?.changeInWC || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[1]?.changeInWC || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[2]?.changeInWC || 0)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </div>
                </div>

                {/* Income Statement Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>Income Statement Assumptions</CardTitle>
                  </CardHeader>
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <Label>Revenue Growth</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.revenueMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, revenueMethod: value as "stable" | "step" | "manual" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="manual">Manual</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.revenueMethod === "stable" && (
                      <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.revenueStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, revenueStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.revenueMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.revenueStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, revenueStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.revenueMethod === "manual" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1} - %`}
                                value={wizardData.revenueValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.revenueValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, revenueValues: newValues });
                                }}
                              />
                            ))}
                    </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Gross Margin</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.grossMarginMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, grossMarginMethod: value as "stable" | "step" | "manual" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="manual">Manual</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.grossMarginMethod === "stable" && (
                      <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.grossMarginStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, grossMarginStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.grossMarginMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.grossMarginStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, grossMarginStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.grossMarginMethod === "manual" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.grossMarginValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.grossMarginValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, grossMarginValues: newValues });
                                }}
                              />
                            ))}
                    </div>
                        )}
                  </div>
                </div>

                    <div className="space-y-2">
                      <Label>Operating Margin</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.operatingMarginMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, operatingMarginMethod: value as "stable" | "step" | "manual" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="manual">Manual</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.operatingMarginMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.operatingMarginStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, operatingMarginStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.operatingMarginMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.operatingMarginStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, operatingMarginStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.operatingMarginMethod === "manual" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.operatingMarginValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.operatingMarginValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, operatingMarginValues: newValues });
                                }}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Tax Rate</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.taxRateMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, taxRateMethod: value as "stable" | "step" | "manual" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="manual">Manual</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.taxRateMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.taxRateStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, taxRateStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.taxRateMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.taxRateStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, taxRateStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.taxRateMethod === "manual" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.taxRateValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.taxRateValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, taxRateValues: newValues });
                                }}
                              />
                    ))}
                  </div>
                        )}
                </div>
                    </div>
                  </div>
                </div>

                {/* Balance Sheet Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>Balance Sheet Assumptions</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Depreciation as % of PPE</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.depreciationMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, depreciationMethod: value as "stable" | "step" | "custom" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="custom">Custom</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.depreciationMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.depreciationStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, depreciationStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.depreciationMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.depreciationStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, depreciationStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.depreciationMethod === "custom" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.depreciationValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.depreciationValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, depreciationValues: newValues });
                                }}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Total Debt Amount</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.totalDebtMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, totalDebtMethod: value as "stable" | "step" | "custom" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="custom">Custom</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.totalDebtMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="Value"
                            value={wizardData.totalDebtStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, totalDebtStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.totalDebtMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.totalDebtStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, totalDebtStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.totalDebtMethod === "custom" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.totalDebtValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.totalDebtValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, totalDebtValues: newValues });
                                }}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Inventory (% of Sales)</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.inventoryMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, inventoryMethod: value as "stable" | "step" | "custom" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="custom">Custom</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.inventoryMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.inventoryStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, inventoryStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.inventoryMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.inventoryStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, inventoryStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.inventoryMethod === "custom" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.inventoryValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.inventoryValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, inventoryValues: newValues });
                                }}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>% Change in Total Debt (increase/decrease)</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.debtChangeMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, debtChangeMethod: value as "stable" | "step" | "custom" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="custom">Custom</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.debtChangeMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.debtChangeStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, debtChangeStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.debtChangeMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.debtChangeStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, debtChangeStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.debtChangeMethod === "custom" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.debtChangeValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.debtChangeValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, debtChangeValues: newValues });
                                }}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                </div>
                </div>

                {/* Cash Flow Statement Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>Cash Flow Statement Assumptions</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>CAPEX</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.capexMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, capexMethod: value as "revenue" | "depreciation" })}
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="revenue">% Revenue</SelectItem>
                            <SelectItem value="depreciation">% Depreciation</SelectItem>
                          </SelectContent>
                        </Select>
                        <Input
                          type="number"
                          placeholder="Percentage"
                          value={wizardData.capexValue}
                          onChange={(e) => setWizardData({ ...wizardData, capexValue: e.target.value })}
                          className="flex-1"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Change in WC</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.changeInWCMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, changeInWCMethod: value as "stable" | "step" | "manual" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="stable">Stable</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                            <SelectItem value="manual">Manual</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.changeInWCMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.changeInWCStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, changeInWCStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.changeInWCMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.changeInWCStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, changeInWCStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.changeInWCMethod === "manual" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.changeInWCValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.changeInWCValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, changeInWCValues: newValues });
                                }}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="repurchases">Share Repurchases</Label>
                      <Input
                        id="repurchases"
                        type="number"
                        placeholder="e.g., 5000"
                        value={wizardData.shareRepurchases}
                        onChange={(e) => setWizardData({ ...wizardData, shareRepurchases: e.target.value })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="dividend">Dividend as % of Net Income</Label>
                      <Input
                        id="dividend"
                        type="number"
                        placeholder="e.g., 25"
                        value={wizardData.dividendPercentNI}
                        onChange={(e) => setWizardData({ ...wizardData, dividendPercentNI: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground">Recommended: 3-5 years</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="deferredTax">Deferred Tax Expense (% of Tax)</Label>
                      <Input
                        id="deferredTax"
                        type="number"
                        placeholder="% of tax"
                        value={wizardData.deferredTaxPercent}
                        onChange={(e) => setWizardData({ ...wizardData, deferredTaxPercent: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground">Recommended: 5 years</p>
                    </div>
                  </div>
                </div>

                {/* DCF Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>DCF Model Assumptions</CardTitle>
                    <p className="text-sm font-semibold mt-1">Base Assumptions</p>
                  </CardHeader>
                  <div className="space-y-4">
                  <div className="space-y-2">
                      <Label>Beta</Label>
                      <div className="flex gap-2">
                        <div className="space-y-2 flex-1">
                          <Label>Method</Label>
                          <Select
                            value={wizardData.betaMethod}
                            onValueChange={(value) => setWizardData({ ...wizardData, betaMethod: value as "calculate" | "manual" })}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="calculate">Calculate</SelectItem>
                              <SelectItem value="manual">Manual</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2 flex-1">
                          <Label>Years</Label>
                          <Select
                            value={wizardData.betaYears}
                            onValueChange={(value) => setWizardData({ ...wizardData, betaYears: value as "1" | "3" | "5" })}
                            disabled={wizardData.betaMethod === "manual"}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="1">1</SelectItem>
                              <SelectItem value="3">3</SelectItem>
                              <SelectItem value="5">5</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2 flex-1">
                          <Label>Benchmark</Label>
                          <Select
                            value={wizardData.betaBenchmark}
                            onValueChange={(value) => setWizardData({ ...wizardData, betaBenchmark: value as "S&P 500" | "NASDAQ" | "Russell 2000" | "Dow Jones" })}
                            disabled={wizardData.betaMethod === "manual"}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="S&P 500">S&P 500</SelectItem>
                              <SelectItem value="NASDAQ">NASDAQ</SelectItem>
                              <SelectItem value="Russell 2000">Russell 2000</SelectItem>
                              <SelectItem value="Dow Jones">Dow Jones</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {wizardData.betaMethod === "manual" && (
                        <div className="space-y-2">
                          <Input
                            type="number"
                            placeholder="e.g., 1.2"
                            value={wizardData.beta}
                            onChange={(e) => setWizardData({ ...wizardData, beta: e.target.value })}
                          />
                          {wizardData.betaReference && (
                            <Badge variant="secondary" className="flex items-center w-fit">
                              Reference: {wizardData.betaReference}
                            </Badge>
                          )}
                        </div>
                      )}

                      {wizardData.betaMethod === "calculate" && wizardData.betaCalculated && (
                        <div className="px-3 py-2 bg-muted rounded-md border border-input text-sm">
                          {wizardData.betaCalculated}
                        </div>
                      )}
                      
                      <p className="text-xs text-muted-foreground">Reference value will be calculated from API if available</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="mrp">Market Risk Premium</Label>
                      <Input
                        id="mrp"
                        type="number"
                        placeholder="6.0"
                        value={wizardData.marketRiskPremium}
                        onChange={(e) => setWizardData({ ...wizardData, marketRiskPremium: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground">Default: 6.0%</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="rfr">Risk-Free Rate</Label>
                      <Input
                        id="rfr"
                        type="number"
                        placeholder="2.5"
                        value={wizardData.riskFreeRate}
                        onChange={(e) => setWizardData({ ...wizardData, riskFreeRate: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground">Will be autopopulated via API when available</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="tgr">Terminal Growth Rate</Label>
                      <Input
                        id="tgr"
                        type="number"
                        placeholder="2.5"
                        value={wizardData.terminalGrowthRate}
                        onChange={(e) => setWizardData({ ...wizardData, terminalGrowthRate: e.target.value })}
                      />
                    </div>

                    <div className="space-y-4">
                      <Label>Scenario</Label>
                      <div className="flex gap-2 w-full">
                        <Button
                          type="button"
                          variant={wizardData.scenario === "bear" ? "default" : "outline"}
                          className={`flex-1 ${wizardData.scenario === "bear" ? "bg-denari-3 hover:bg-denari-3/90" : ""}`}
                          onClick={() => setWizardData({ ...wizardData, scenario: "bear" })}
                        >
                          Bear
                        </Button>
                        <Button
                          type="button"
                          variant={wizardData.scenario === "bull" ? "default" : "outline"}
                          className={`flex-1 ${wizardData.scenario === "bull" ? "bg-denari-3 hover:bg-denari-3/90" : ""}`}
                          onClick={() => setWizardData({ ...wizardData, scenario: "bull" })}
                        >
                          Bull
                        </Button>
                      </div>
                      
                      {/* Bear/Bull Scenario Assumptions */}
                      {wizardData.scenario === "bear" && (
                        <div className="space-y-4 pt-4 border-t">
                          <h4 className="font-semibold text-sm">Bear Scenario Assumptions</h4>
                          
                          <div className="space-y-2">
                            <Label>Revenue Growth</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bearRevenueMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bearRevenueMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bearRevenueMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bearRevenueStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearRevenueStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearRevenueMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bearRevenueStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearRevenueStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearRevenueMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1} - %`}
                                      value={wizardData.bearRevenueValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bearRevenueValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bearRevenueValues: newValues });
                                      }}
                                    />
                    ))}
                  </div>
                              )}
                </div>
                          </div>

                          <div className="space-y-2">
                            <Label>Gross Margin</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bearGrossMarginMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bearGrossMarginMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bearGrossMarginMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bearGrossMarginStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearGrossMarginStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearGrossMarginMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bearGrossMarginStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearGrossMarginStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearGrossMarginMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1}`}
                                      value={wizardData.bearGrossMarginValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bearGrossMarginValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bearGrossMarginValues: newValues });
                                      }}
                                    />
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label>Operating Margin</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bearOperatingMarginMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bearOperatingMarginMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bearOperatingMarginMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bearOperatingMarginStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearOperatingMarginStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearOperatingMarginMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bearOperatingMarginStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearOperatingMarginStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearOperatingMarginMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1}`}
                                      value={wizardData.bearOperatingMarginValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bearOperatingMarginValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bearOperatingMarginValues: newValues });
                                      }}
                                    />
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label>Tax Rate</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bearTaxRateMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bearTaxRateMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bearTaxRateMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bearTaxRateStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearTaxRateStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearTaxRateMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bearTaxRateStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearTaxRateStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearTaxRateMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1}`}
                                      value={wizardData.bearTaxRateValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bearTaxRateValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bearTaxRateValues: newValues });
                                      }}
                                    />
                                  ))}
                                </div>
                              )}
                            </div>
                  </div>

                    <div className="space-y-2">
                            <Label htmlFor="depreciation-bear-scenario">Depreciation as % of PPE</Label>
                            <Input
                              id="depreciation-bear-scenario"
                              type="number"
                              placeholder="e.g., 10"
                              value={wizardData.depreciationPercentPPE}
                              onChange={(e) => setWizardData({ ...wizardData, depreciationPercentPPE: e.target.value })}
                            />
                          </div>

                    <div className="space-y-2">
                            <Label>CAPEX</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bearCapexMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bearCapexMethod: value as "revenue" | "depreciation" })}
                              >
                                <SelectTrigger className="w-40">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="revenue">% Revenue</SelectItem>
                                  <SelectItem value="depreciation">% Depreciation</SelectItem>
                                </SelectContent>
                              </Select>
                              <Input
                                type="number"
                                placeholder="Percentage"
                                value={wizardData.bearCapexValue}
                                onChange={(e) => setWizardData({ ...wizardData, bearCapexValue: e.target.value })}
                                className="flex-1"
                              />
                            </div>
                          </div>

                    <div className="space-y-2">
                            <Label>Change in WC</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bearChangeInWCMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bearChangeInWCMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bearChangeInWCMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bearChangeInWCStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearChangeInWCStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearChangeInWCMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bearChangeInWCStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bearChangeInWCStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bearChangeInWCMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1}`}
                                      value={wizardData.bearChangeInWCValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bearChangeInWCValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bearChangeInWCValues: newValues });
                                      }}
                                    />
                                  ))}
                            </div>
                              )}
                            </div>
                          </div>

                          {/* Base Assumptions for Bear Scenario */}
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label>Beta</Label>
                              <div className="flex gap-2">
                                <div className="space-y-2 flex-1">
                                  <Label>Method</Label>
                                  <Select
                                    value={wizardData.betaMethod}
                                    onValueChange={(value) => setWizardData({ ...wizardData, betaMethod: value as "calculate" | "manual" })}
                                  >
                                    <SelectTrigger className="w-full">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="calculate">Calculate</SelectItem>
                                      <SelectItem value="manual">Manual</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>

                                <div className="space-y-2 flex-1">
                                  <Label>Years</Label>
                                  <Select
                                    value={wizardData.betaYears}
                                    onValueChange={(value) => setWizardData({ ...wizardData, betaYears: value as "1" | "3" | "5" })}
                                    disabled={wizardData.betaMethod === "manual"}
                                  >
                                    <SelectTrigger className="w-full">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="1">1</SelectItem>
                                      <SelectItem value="3">3</SelectItem>
                                      <SelectItem value="5">5</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>

                                <div className="space-y-2 flex-1">
                                  <Label>Benchmark</Label>
                                  <Select
                                    value={wizardData.betaBenchmark}
                                    onValueChange={(value) => setWizardData({ ...wizardData, betaBenchmark: value as "S&P 500" | "NASDAQ" | "Russell 2000" | "Dow Jones" })}
                                    disabled={wizardData.betaMethod === "manual"}
                                  >
                                    <SelectTrigger className="w-full">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="S&P 500">S&P 500</SelectItem>
                                      <SelectItem value="NASDAQ">NASDAQ</SelectItem>
                                      <SelectItem value="Russell 2000">Russell 2000</SelectItem>
                                      <SelectItem value="Dow Jones">Dow Jones</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>

                              {wizardData.betaMethod === "manual" && (
                                <div className="space-y-2">
                                  <Input
                                    type="number"
                                    placeholder="e.g., 1.2"
                                    value={wizardData.beta}
                                    onChange={(e) => setWizardData({ ...wizardData, beta: e.target.value })}
                                  />
                                  {wizardData.betaReference && (
                                    <Badge variant="secondary" className="flex items-center w-fit">
                                      Reference: {wizardData.betaReference}
                                    </Badge>
                                  )}
                                </div>
                              )}

                              {wizardData.betaMethod === "calculate" && wizardData.betaCalculated && (
                                <div className="px-3 py-2 bg-muted rounded-md border border-input text-sm">
                                  {wizardData.betaCalculated}
                                </div>
                              )}
                              
                              <p className="text-xs text-muted-foreground">Reference value will be calculated from API if available</p>
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="mrp-bear">Market Risk Premium</Label>
                              <Input
                                id="mrp-bear"
                                type="number"
                                placeholder="6.0"
                                value={wizardData.marketRiskPremium}
                                onChange={(e) => setWizardData({ ...wizardData, marketRiskPremium: e.target.value })}
                              />
                              <p className="text-xs text-muted-foreground">Default: 6.0%</p>
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="rfr-bear">Risk-Free Rate</Label>
                              <Input
                                id="rfr-bear"
                                type="number"
                                placeholder="2.5"
                                value={wizardData.riskFreeRate}
                                onChange={(e) => setWizardData({ ...wizardData, riskFreeRate: e.target.value })}
                              />
                              <p className="text-xs text-muted-foreground">Will be autopopulated via API when available</p>
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="tgr-bear">Terminal Growth Rate</Label>
                              <Input
                                id="tgr-bear"
                                type="number"
                                placeholder="2.5"
                                value={wizardData.terminalGrowthRate}
                                onChange={(e) => setWizardData({ ...wizardData, terminalGrowthRate: e.target.value })}
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      {wizardData.scenario === "bull" && (
                        <div className="space-y-4 pt-4 border-t">
                          <h4 className="font-semibold text-sm">Bull Scenario Assumptions</h4>
                          
                          <div className="space-y-2">
                            <Label>Revenue Growth</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bullRevenueMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bullRevenueMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bullRevenueMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bullRevenueStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullRevenueStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullRevenueMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bullRevenueStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullRevenueStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullRevenueMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1} - %`}
                                      value={wizardData.bullRevenueValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bullRevenueValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bullRevenueValues: newValues });
                                      }}
                                    />
                          ))}
                        </div>
                              )}
                            </div>
                    </div>

                          <div className="space-y-2">
                            <Label>Gross Margin</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bullGrossMarginMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bullGrossMarginMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bullGrossMarginMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bullGrossMarginStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullGrossMarginStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullGrossMarginMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bullGrossMarginStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullGrossMarginStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullGrossMarginMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1}`}
                                      value={wizardData.bullGrossMarginValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bullGrossMarginValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bullGrossMarginValues: newValues });
                                      }}
                                    />
                                  ))}
                          </div>
                              )}
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label>Operating Margin</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bullOperatingMarginMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bullOperatingMarginMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bullOperatingMarginMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bullOperatingMarginStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullOperatingMarginStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullOperatingMarginMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bullOperatingMarginStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullOperatingMarginStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullOperatingMarginMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1}`}
                                      value={wizardData.bullOperatingMarginValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bullOperatingMarginValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bullOperatingMarginValues: newValues });
                                      }}
                                    />
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                          <div className="space-y-2">
                            <Label>Tax Rate</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bullTaxRateMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bullTaxRateMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bullTaxRateMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bullTaxRateStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullTaxRateStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullTaxRateMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bullTaxRateStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullTaxRateStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullTaxRateMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1}`}
                                      value={wizardData.bullTaxRateValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bullTaxRateValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bullTaxRateValues: newValues });
                                      }}
                                    />
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="depreciation-bull-scenario">Depreciation as % of PPE</Label>
                            <Input
                              id="depreciation-bull-scenario"
                              type="number"
                              placeholder="e.g., 10"
                              value={wizardData.depreciationPercentPPE}
                              onChange={(e) => setWizardData({ ...wizardData, depreciationPercentPPE: e.target.value })}
                            />
                          </div>

                          <div className="space-y-2">
                            <Label>CAPEX</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bullCapexMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bullCapexMethod: value as "revenue" | "depreciation" })}
                              >
                                <SelectTrigger className="w-40">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="revenue">% Revenue</SelectItem>
                                  <SelectItem value="depreciation">% Depreciation</SelectItem>
                                </SelectContent>
                              </Select>
                              <Input
                                type="number"
                                placeholder="Percentage"
                                value={wizardData.bullCapexValue}
                                onChange={(e) => setWizardData({ ...wizardData, bullCapexValue: e.target.value })}
                                className="flex-1"
                              />
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label>Change in WC</Label>
                            <div className="flex gap-2">
                              <Select
                                value={wizardData.bullChangeInWCMethod}
                                onValueChange={(value) => setWizardData({ ...wizardData, bullChangeInWCMethod: value as "stable" | "step" | "manual" })}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="stable">Stable</SelectItem>
                                  <SelectItem value="step">Step Change</SelectItem>
                                  <SelectItem value="manual">Manual</SelectItem>
                                </SelectContent>
                              </Select>
                              {wizardData.bullChangeInWCMethod === "stable" && (
                                <Input
                                  type="number"
                                  placeholder="%"
                                  value={wizardData.bullChangeInWCStableValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullChangeInWCStableValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullChangeInWCMethod === "step" && (
                                <Input
                                  type="number"
                                  placeholder="Step rate %"
                                  value={wizardData.bullChangeInWCStepValue}
                                  onChange={(e) => setWizardData({ ...wizardData, bullChangeInWCStepValue: e.target.value })}
                                  className="flex-1"
                                />
                              )}
                              {wizardData.bullChangeInWCMethod === "manual" && (
                                <div className="flex gap-2 flex-1">
                                  {[0, 1, 2, 3, 4].map((year) => (
                                    <Input
                                      key={year}
                                      type="number"
                                      placeholder={`Y${year + 1}`}
                                      value={wizardData.bullChangeInWCValues[year]}
                                      onChange={(e) => {
                                        const newValues = [...wizardData.bullChangeInWCValues];
                                        newValues[year] = e.target.value;
                                        setWizardData({ ...wizardData, bullChangeInWCValues: newValues });
                                      }}
                                    />
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Base Assumptions for Bull Scenario */}
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label>Beta</Label>
                              <div className="flex gap-2">
                                <div className="space-y-2 flex-1">
                                  <Label>Method</Label>
                                  <Select
                                    value={wizardData.betaMethod}
                                    onValueChange={(value) => setWizardData({ ...wizardData, betaMethod: value as "calculate" | "manual" })}
                                  >
                                    <SelectTrigger className="w-full">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="calculate">Calculate</SelectItem>
                                      <SelectItem value="manual">Manual</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>

                                <div className="space-y-2 flex-1">
                                  <Label>Years</Label>
                                  <Select
                                    value={wizardData.betaYears}
                                    onValueChange={(value) => setWizardData({ ...wizardData, betaYears: value as "1" | "3" | "5" })}
                                    disabled={wizardData.betaMethod === "manual"}
                                  >
                                    <SelectTrigger className="w-full">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="1">1</SelectItem>
                                      <SelectItem value="3">3</SelectItem>
                                      <SelectItem value="5">5</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>

                                <div className="space-y-2 flex-1">
                                  <Label>Benchmark</Label>
                                  <Select
                                    value={wizardData.betaBenchmark}
                                    onValueChange={(value) => setWizardData({ ...wizardData, betaBenchmark: value as "S&P 500" | "NASDAQ" | "Russell 2000" | "Dow Jones" })}
                                    disabled={wizardData.betaMethod === "manual"}
                                  >
                                    <SelectTrigger className="w-full">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="S&P 500">S&P 500</SelectItem>
                                      <SelectItem value="NASDAQ">NASDAQ</SelectItem>
                                      <SelectItem value="Russell 2000">Russell 2000</SelectItem>
                                      <SelectItem value="Dow Jones">Dow Jones</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>

                              {wizardData.betaMethod === "manual" && (
                                <div className="space-y-2">
                                  <Input
                                    type="number"
                                    placeholder="e.g., 1.2"
                                    value={wizardData.beta}
                                    onChange={(e) => setWizardData({ ...wizardData, beta: e.target.value })}
                                  />
                                  {wizardData.betaReference && (
                                    <Badge variant="secondary" className="flex items-center w-fit">
                                      Reference: {wizardData.betaReference}
                                    </Badge>
                                  )}
                                </div>
                              )}

                              {wizardData.betaMethod === "calculate" && wizardData.betaCalculated && (
                                <div className="px-3 py-2 bg-muted rounded-md border border-input text-sm">
                                  {wizardData.betaCalculated}
                                </div>
                              )}
                              
                              <p className="text-xs text-muted-foreground">Reference value will be calculated from API if available</p>
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="mrp-bull">Market Risk Premium</Label>
                              <Input
                                id="mrp-bull"
                                type="number"
                                placeholder="6.0"
                                value={wizardData.marketRiskPremium}
                                onChange={(e) => setWizardData({ ...wizardData, marketRiskPremium: e.target.value })}
                              />
                              <p className="text-xs text-muted-foreground">Default: 6.0%</p>
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="rfr-bull">Risk-Free Rate</Label>
                              <Input
                                id="rfr-bull"
                                type="number"
                                placeholder="2.5"
                                value={wizardData.riskFreeRate}
                                onChange={(e) => setWizardData({ ...wizardData, riskFreeRate: e.target.value })}
                              />
                              <p className="text-xs text-muted-foreground">Will be autopopulated via API when available</p>
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="tgr-bull">Terminal Growth Rate</Label>
                              <Input
                                id="tgr-bull"
                                type="number"
                                placeholder="2.5"
                                value={wizardData.terminalGrowthRate}
                                onChange={(e) => setWizardData({ ...wizardData, terminalGrowthRate: e.target.value })}
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Relative Valuation Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>Relative Valuation Assumptions</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Select Competitors</Label>
                      <div className="space-y-2">
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button variant="outline" className="w-full justify-start">
                              Add Competitor
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-[400px] p-0" align="start">
                            <Command>
                              <CommandInput placeholder="Search competitors..." />
                              <CommandList>
                                <CommandEmpty>No companies found.</CommandEmpty>
                                <CommandGroup>
                                  {mockCompanies.filter(c => c.ticker !== wizardData.ticker).map((company) => (
                                    <CommandItem
                                      key={company.ticker}
                                      value={`${company.name} ${company.ticker}`}
                                      onSelect={() => {
                                        if (!wizardData.competitors.includes(company.ticker)) {
                                          setWizardData({
                                            ...wizardData,
                                            competitors: [...wizardData.competitors, company.ticker],
                                          });
                                        }
                                      }}
                                    >
                                      <div className="flex flex-col">
                                        <span className="font-medium">{company.name}</span>
                                        <span className="text-xs text-muted-foreground">{company.ticker}</span>
                    </div>
                                    </CommandItem>
                                  ))}
                                </CommandGroup>
                              </CommandList>
                            </Command>
                          </PopoverContent>
                        </Popover>
                        <div className="flex flex-wrap gap-2">
                          {wizardData.competitors.map((ticker) => {
                            const company = mockCompanies.find(c => c.ticker === ticker);
                            return (
                              <Badge key={ticker} variant="secondary" className="flex items-center gap-2">
                                {company?.name || ticker}
                                <X
                                  className="h-3 w-3 cursor-pointer"
                                  onClick={() => {
                                    setWizardData({
                                      ...wizardData,
                                      competitors: wizardData.competitors.filter(c => c !== ticker),
                                    });
                                  }}
                                />
                              </Badge>
                            );
                          })}
                    </div>
                  </div>
                      <p className="text-xs text-muted-foreground">
                        For each competitor, we will pull or compute: Market Cap, Revenue, EBITDA, Earnings, EV, Price/Sales, P/E, EV/EBITDA, EV/Revenue
                      </p>
                </div>
                  </div>
                </div>

                {/* Generate Button */}
                <div className="flex justify-end pt-6 border-t">
                  <Button onClick={handleFinish} className="bg-primary hover:bg-primary/90" size="lg">
                    Generate Valuation
                </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

