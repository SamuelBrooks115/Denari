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

export default function NewProjectWizard() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCompany, setSelectedCompany] = useState<{ name: string; ticker: string } | null>(null);
  const [open, setOpen] = useState(false);
  
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
    ebitdaMarginMethod: "step" as "stable" | "step" | "manual",
    ebitdaMarginStableValue: "",
    ebitdaMarginStepValue: "",
    ebitdaMarginValues: ["", "", "", "", ""],
    taxRateMethod: "step" as "stable" | "step" | "manual",
    taxRateStableValue: "",
    taxRateStepValue: "",
    taxRateValues: ["", "", "", "", ""],
    interestRateMethod: "stable" as "stable" | "step" | "custom",
    interestRateStableValue: "",
    interestRateStepValue: "",
    interestRateValues: ["", "", "", "", ""],
    // Balance Sheet
    depreciationPercentPPE: "",
    totalDebt: "",
    inventoryMethod: "percent" as "percent" | "step",
    inventoryPercent: "",
    cash: "",
    debtChangePercent: "",
    // Cash Flow
    shareRepurchases: "",
    dividendPercentNI: "",
    deferredTaxMethod: "percent" as "percent",
    deferredTaxPercent: "",
    capexMethod: "revenue" as "revenue" | "depreciation",
    capexValue: "",
    // DCF
    betaMethod: "manual" as "calculate" | "manual",
    beta: "",
    betaCalculated: "",
    betaReference: "",
    marketRiskPremium: "6.0",
    riskFreeRate: "2.5",
    terminalGrowthRate: "2.5",
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
      { year: "2022", revenue: 125000, grossProfit: 62500, operatingExpenses: 37500, ebitda: 25000, netIncome: 18750 },
      { year: "2023", revenue: 142000, grossProfit: 72100, operatingExpenses: 42600, ebitda: 29500, netIncome: 22130 },
      { year: "2024", revenue: 165000, grossProfit: 85800, operatingExpenses: 49500, ebitda: 36300, netIncome: 27225 },
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
                          <TableCell className="font-medium">Gross Profit</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[0]?.grossProfit || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[1]?.grossProfit || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[2]?.grossProfit || 0)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Operating Expenses</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[0]?.operatingExpenses || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[1]?.operatingExpenses || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[2]?.operatingExpenses || 0)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">EBITDA</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[0]?.ebitda || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[1]?.ebitda || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[2]?.ebitda || 0)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Net Income</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[0]?.netIncome || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[1]?.netIncome || 0)}</TableCell>
                          <TableCell className="text-right">${formatNumber(historicalFinancials.income[2]?.netIncome || 0)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </div>
                </div>

                {/* Income Statement Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>Income Statement Inputs</CardTitle>
                  </CardHeader>
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <Label>Revenue</Label>
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
                            placeholder="Value"
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
                                placeholder={`Y${year + 1}`}
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
                            placeholder="Margin %"
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
                            placeholder="Margin %"
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
                      <Label>EBITDA Margin</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.ebitdaMarginMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, ebitdaMarginMethod: value as "stable" | "step" | "manual" })}
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
                        {wizardData.ebitdaMarginMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="Margin %"
                            value={wizardData.ebitdaMarginStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, ebitdaMarginStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.ebitdaMarginMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.ebitdaMarginStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, ebitdaMarginStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.ebitdaMarginMethod === "manual" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.ebitdaMarginValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.ebitdaMarginValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, ebitdaMarginValues: newValues });
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
                            placeholder="Tax %"
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

                    <div className="space-y-2">
                      <Label>Interest Rate on Debt</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.interestRateMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, interestRateMethod: value as "stable" | "step" | "custom" })}
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
                        {wizardData.interestRateMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="Interest rate %"
                            value={wizardData.interestRateStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, interestRateStableValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.interestRateMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.interestRateStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, interestRateStepValue: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        {wizardData.interestRateMethod === "custom" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1}`}
                                value={wizardData.interestRateValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.interestRateValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, interestRateValues: newValues });
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
                    <CardTitle>Balance Sheet Inputs</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="depreciation">Depreciation as % of PPE</Label>
                      <Input
                        id="depreciation"
                        type="number"
                        placeholder="e.g., 10"
                        value={wizardData.depreciationPercentPPE}
                        onChange={(e) => setWizardData({ ...wizardData, depreciationPercentPPE: e.target.value })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="debt">Total Debt Amount</Label>
                      <Input
                        id="debt"
                        type="number"
                        placeholder="e.g., 50000"
                        value={wizardData.totalDebt}
                        onChange={(e) => setWizardData({ ...wizardData, totalDebt: e.target.value })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Inventory</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.inventoryMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, inventoryMethod: value as "percent" | "step" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="percent">% of Sales</SelectItem>
                            <SelectItem value="step">Step Change</SelectItem>
                          </SelectContent>
                        </Select>
                        <Input
                          type="number"
                          placeholder={wizardData.inventoryMethod === "percent" ? "% of sales" : "Step rate %"}
                          value={wizardData.inventoryPercent}
                          onChange={(e) => setWizardData({ ...wizardData, inventoryPercent: e.target.value })}
                          className="flex-1"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="debtChange">% Change in Total Debt (increase/decrease)</Label>
                      <Input
                        id="debtChange"
                        type="number"
                        placeholder="e.g., 5 or -5"
                        value={wizardData.debtChangePercent}
                        onChange={(e) => setWizardData({ ...wizardData, debtChangePercent: e.target.value })}
                      />
                    </div>
                  </div>
                </div>

                {/* Cash Flow Statement Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>Cash Flow Statement Inputs</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
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
                    </div>

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
                  </div>
                </div>

                {/* DCF Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>DCF Model Inputs</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Beta</Label>
                      <div className="flex gap-2">
                        <Select
                          value={wizardData.betaMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, betaMethod: value as "calculate" | "manual" })}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="calculate">Calculate</SelectItem>
                            <SelectItem value="manual">Manual</SelectItem>
                          </SelectContent>
                        </Select>
                        {wizardData.betaMethod === "calculate" ? (
                          <div className="flex-1 px-3 py-2 bg-muted rounded-md border border-input text-sm">
                            {wizardData.betaCalculated || "Calculated value will appear here"}
                          </div>
                        ) : (
                          <div className="flex gap-2 flex-1">
                            <Input
                              type="number"
                              placeholder="e.g., 1.2"
                              value={wizardData.beta}
                              onChange={(e) => setWizardData({ ...wizardData, beta: e.target.value })}
                              className="flex-1"
                            />
                            {wizardData.betaReference && (
                              <Badge variant="secondary" className="flex items-center">
                                Reference: {wizardData.betaReference}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
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
                  </div>
                </div>

                {/* Relative Valuation Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>Relative Valuation Inputs</CardTitle>
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
