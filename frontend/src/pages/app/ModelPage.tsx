import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Download, RefreshCw, Settings, TrendingUp, FileSpreadsheet } from "lucide-react";
import { useState } from "react";

export default function ModelPage() {
  const [period, setPeriod] = useState("annual");
  const [view, setView] = useState("actual");

  // Mock financial data
  const incomeStatementData = [
    { item: "Revenue", fy2022: 125000, fy2023: 142000, fy2024: 165000, q1_2025: 43000, q2_2025: 47000 },
    { item: "Cost of Revenue", fy2022: -62500, fy2023: -69900, fy2024: -79200, q1_2025: -20640, q2_2025: -22560 },
    { item: "Gross Profit", fy2022: 62500, fy2023: 72100, fy2024: 85800, q1_2025: 22360, q2_2025: 24440 },
    { item: "Operating Expenses", fy2022: -37500, fy2023: -42600, fy2024: -49500, q1_2025: -12900, q2_2025: -14100 },
    { item: "EBITDA", fy2022: 25000, fy2023: 29500, fy2024: 36300, q1_2025: 9460, q2_2025: 10340 },
    { item: "Net Income", fy2022: 18750, fy2023: 22130, fy2024: 27225, q1_2025: 7095, q2_2025: 7755 },
  ];

  const balanceSheetData = [
    { item: "Cash & Equivalents", fy2022: 45000, fy2023: 52000, fy2024: 63000, q1_2025: 67000, q2_2025: 71000 },
    { item: "Accounts Receivable", fy2022: 22000, fy2023: 26000, fy2024: 31000, q1_2025: 33000, q2_2025: 35000 },
    { item: "Inventory", fy2022: 18000, fy2023: 21000, fy2024: 24000, q1_2025: 25000, q2_2025: 26000 },
    { item: "Total Assets", fy2022: 185000, fy2023: 220000, fy2024: 265000, q1_2025: 280000, q2_2025: 295000 },
    { item: "Total Liabilities", fy2022: 85000, fy2023: 95000, fy2024: 105000, q1_2025: 108000, q2_2025: 110000 },
    { item: "Stockholders' Equity", fy2022: 100000, fy2023: 125000, fy2024: 160000, q1_2025: 172000, q2_2025: 185000 },
  ];

  const cashFlowData = [
    { item: "Operating Cash Flow", fy2022: 22000, fy2023: 27000, fy2024: 34000, q1_2025: 9000, q2_2025: 10000 },
    { item: "Investing Cash Flow", fy2022: -8000, fy2023: -10000, fy2024: -12000, q1_2025: -3000, q2_2025: -3500 },
    { item: "Financing Cash Flow", fy2022: -5000, fy2023: -6000, fy2024: -7000, q1_2025: -2000, q2_2025: -2000 },
    { item: "Net Change in Cash", fy2022: 9000, fy2023: 11000, fy2024: 15000, q1_2025: 4000, q2_2025: 4500 },
  ];

  const valuationData = [
    { metric: "Enterprise Value", value: "425M", change: "+12.5%" },
    { metric: "Equity Value", value: "388M", change: "+14.2%" },
    { metric: "DCF Value per Share", value: "$42.50", change: "+8.3%" },
    { metric: "P/E Ratio", value: "18.5x", change: "-2.1%" },
    { metric: "EV/EBITDA", value: "12.3x", change: "+1.8%" },
    { metric: "Price to Book", value: "2.8x", change: "+5.4%" },
  ];

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-denari-1">Main Model</h1>
              <p className="text-muted-foreground mt-1">AAPL - Apple Inc.</p>
            </div>
            <div className="flex items-center gap-3">
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="quarterly">Quarterly</SelectItem>
                  <SelectItem value="annual">Annual</SelectItem>
                </SelectContent>
              </Select>
              <Select value={view} onValueChange={setView}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="actual">Actual</SelectItem>
                  <SelectItem value="forecast">Forecast</SelectItem>
                  <SelectItem value="combined">Combined</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Button size="sm" className="bg-denari-3 hover:bg-denari-3/90">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">Last Updated: Jan 15, 2025</Badge>
            <Badge variant="outline" className="border-denari-5 text-denari-5">Status: Active</Badge>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="income" className="space-y-6">
          <TabsList className="bg-denari-2/10">
            <TabsTrigger value="income">Income Statement</TabsTrigger>
            <TabsTrigger value="balance">Balance Sheet</TabsTrigger>
            <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
            <TabsTrigger value="dcf">DCF Analysis</TabsTrigger>
            <TabsTrigger value="relative">Relative Valuation</TabsTrigger>
          </TabsList>

          {/* Income Statement Tab */}
          <TabsContent value="income" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5 text-denari-3" />
                  Income Statement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-denari-2/5">
                        <TableHead className="font-bold">Item</TableHead>
                        <TableHead className="text-right">FY 2022</TableHead>
                        <TableHead className="text-right">FY 2023</TableHead>
                        <TableHead className="text-right">FY 2024</TableHead>
                        <TableHead className="text-right">Q1 2025</TableHead>
                        <TableHead className="text-right">Q2 2025</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {incomeStatementData.map((row, idx) => (
                        <TableRow key={idx} className={row.item === "Net Income" ? "bg-denari-5/5 font-semibold" : ""}>
                          <TableCell className="font-medium">{row.item}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2022)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2023)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2024)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.q1_2025)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.q2_2025)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Balance Sheet Tab */}
          <TabsContent value="balance" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5 text-denari-3" />
                  Balance Sheet
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-denari-2/5">
                        <TableHead className="font-bold">Item</TableHead>
                        <TableHead className="text-right">FY 2022</TableHead>
                        <TableHead className="text-right">FY 2023</TableHead>
                        <TableHead className="text-right">FY 2024</TableHead>
                        <TableHead className="text-right">Q1 2025</TableHead>
                        <TableHead className="text-right">Q2 2025</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {balanceSheetData.map((row, idx) => (
                        <TableRow key={idx} className={row.item === "Stockholders' Equity" ? "bg-denari-5/5 font-semibold" : ""}>
                          <TableCell className="font-medium">{row.item}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2022)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2023)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2024)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.q1_2025)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.q2_2025)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cash Flow Tab */}
          <TabsContent value="cashflow" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5 text-denari-3" />
                  Cash Flow Statement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-denari-2/5">
                        <TableHead className="font-bold">Item</TableHead>
                        <TableHead className="text-right">FY 2022</TableHead>
                        <TableHead className="text-right">FY 2023</TableHead>
                        <TableHead className="text-right">FY 2024</TableHead>
                        <TableHead className="text-right">Q1 2025</TableHead>
                        <TableHead className="text-right">Q2 2025</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cashFlowData.map((row, idx) => (
                        <TableRow key={idx} className={row.item === "Net Change in Cash" ? "bg-denari-5/5 font-semibold" : ""}>
                          <TableCell className="font-medium">{row.item}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2022)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2023)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.fy2024)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.q1_2025)}</TableCell>
                          <TableCell className="text-right">${formatNumber(row.q2_2025)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* DCF Analysis Tab */}
          <TabsContent value="dcf" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {valuationData.slice(0, 3).map((item, idx) => (
                <Card key={idx}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-muted-foreground">{item.metric}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-denari-1">{item.value}</div>
                    <div className={`flex items-center gap-1 mt-2 text-sm ${item.change.startsWith('+') ? 'text-denari-5' : 'text-red-500'}`}>
                      <TrendingUp className="h-4 w-4" />
                      {item.change}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            <Card>
              <CardHeader>
                <CardTitle>DCF Valuation Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">WACC</p>
                      <p className="text-2xl font-semibold">8.5%</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">Terminal Growth Rate</p>
                      <p className="text-2xl font-semibold">2.5%</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">Forecast Period</p>
                      <p className="text-2xl font-semibold">5 Years</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">Terminal Value</p>
                      <p className="text-2xl font-semibold">$350M</p>
                    </div>
                  </div>
                  <div className="pt-4 border-t">
                    <p className="text-sm text-muted-foreground mb-2">Valuation Range</p>
                    <div className="flex items-center gap-4">
                      <div className="flex-1 bg-gradient-to-r from-denari-5/20 via-denari-3/30 to-denari-6/20 h-8 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium">$35.50 - $49.50</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Relative Valuation Tab */}
          <TabsContent value="relative" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {valuationData.slice(3, 6).map((item, idx) => (
                <Card key={idx}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-muted-foreground">{item.metric}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-denari-1">{item.value}</div>
                    <div className={`flex items-center gap-1 mt-2 text-sm ${item.change.startsWith('+') ? 'text-denari-5' : 'text-red-500'}`}>
                      <TrendingUp className="h-4 w-4" />
                      {item.change}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Peer Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-denari-2/5">
                        <TableHead>Company</TableHead>
                        <TableHead className="text-right">P/E</TableHead>
                        <TableHead className="text-right">EV/EBITDA</TableHead>
                        <TableHead className="text-right">P/B</TableHead>
                        <TableHead className="text-right">Market Cap</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow className="bg-denari-3/5 font-semibold">
                        <TableCell>Apple Inc. (Target)</TableCell>
                        <TableCell className="text-right">18.5x</TableCell>
                        <TableCell className="text-right">12.3x</TableCell>
                        <TableCell className="text-right">2.8x</TableCell>
                        <TableCell className="text-right">$388M</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Peer 1</TableCell>
                        <TableCell className="text-right">22.1x</TableCell>
                        <TableCell className="text-right">14.5x</TableCell>
                        <TableCell className="text-right">3.2x</TableCell>
                        <TableCell className="text-right">$450M</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Peer 2</TableCell>
                        <TableCell className="text-right">16.8x</TableCell>
                        <TableCell className="text-right">11.2x</TableCell>
                        <TableCell className="text-right">2.5x</TableCell>
                        <TableCell className="text-right">$320M</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Peer 3</TableCell>
                        <TableCell className="text-right">19.3x</TableCell>
                        <TableCell className="text-right">13.1x</TableCell>
                        <TableCell className="text-right">2.9x</TableCell>
                        <TableCell className="text-right">$410M</TableCell>
                      </TableRow>
                      <TableRow className="bg-denari-4/10 font-semibold">
                        <TableCell>Industry Average</TableCell>
                        <TableCell className="text-right">19.4x</TableCell>
                        <TableCell className="text-right">12.9x</TableCell>
                        <TableCell className="text-right">2.9x</TableCell>
                        <TableCell className="text-right">$393M</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
