import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Download, RefreshCw, Settings, TrendingUp, FileSpreadsheet } from "lucide-react";
import { useState } from "react";
import { downloadExcelFromTemplate } from "@/lib/downloadExcel";

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

  const handleExport = async () => {
    try {
      // Extract numeric values from valuation data
      const enterpriseValue = parseFloat(valuationData[0].value.replace('M', '')) * 1000000; // Convert "425M" to 425000000
      const equityValue = parseFloat(valuationData[1].value.replace('M', '')) * 1000000; // Convert "388M" to 388000000
      const dcfValuePerShare = parseFloat(valuationData[2].value.replace('$', '')); // Extract 42.50 from "$42.50"
      
      // Calculate Net Debt (Enterprise Value - Equity Value)
      const netDebt = enterpriseValue - equityValue;
      
      // Calculate shares outstanding (Equity Value / Price per share, or use a reasonable estimate)
      // For now, we'll use a placeholder - you may want to add this as actual data
      const estimatedSharePrice = 150; // Placeholder - adjust based on actual data
      const sharesOutstanding = Math.round(equityValue / estimatedSharePrice);
      
      // Map data to DCF template structure
      // NOTE: Cell references are estimates based on typical DCF template layout
      // You MUST verify and adjust these by opening DCF_A_Template.xlsx in Excel
      const dataMap: Record<string, any> = {
        // ===== HEADER SECTION =====
        'B2': 'Apple Inc.',  // Company Name in header (adjust if different)
        
        // ===== OTHER ASSUMPTIONS SECTION (Top Right) =====
        // These are typical locations - adjust based on your template
        //'J2': 'Apple Inc.',  // Company Name
        'J2': 'AAPL',        // Ticker Symbol
        'J5': new Date('2025-12-31'), // Fiscal Year End (12/31/2025)
        //'J5': 0.02,          // LTGR (Long-Term Growth Rate) - 2.00% as decimal
        'J6': balanceSheetData[0].fy2024,  // Cash & Equivalents (most recent year)
        'J7': sharesOutstanding,  // Diluted Shares Outstanding
        'J8': estimatedSharePrice,  // Current Price (placeholder - adjust)
        'J9': equityValue,   // Market Cap (Equity Value)
        'J10': netDebt,      // BV debt (Net Debt)
        
        // ===== FREE CASH FLOW SECTION - HISTORICAL DATA (Year'A' columns) =====
        // Revenue row - Historical years (typically columns C, D, E, F, G for 5 years)
        'D17': incomeStatementData[0].fy2022,  // Revenue Year'A'1 (FY2022)
        'E17': incomeStatementData[0].fy2023, // Revenue Year'A'2 (FY2023)
        'F17': incomeStatementData[0].fy2024,  // Revenue Year'A'3 (FY2024)
        // Add more years if you have data for Year'A'4 and Year'A'5
        
        // (-) COGS row
        'D20': Math.abs(incomeStatementData[1].fy2022),  // COGS Year'A'1 (make positive)
        'E20': Math.abs(incomeStatementData[1].fy2023), // COGS Year'A'2
        'F20': Math.abs(incomeStatementData[1].fy2024), // COGS Year'A'3
        
        // Gross Profit (calculated in template, but can set if needed)
        // 'C12': incomeStatementData[2].fy2022,  // GP Year'A'1
        
        // (-) Operating Expenses row
        'D23': Math.abs(incomeStatementData[3].fy2022),  // Op Ex Year'A'1 (make positive)
        'E23': Math.abs(incomeStatementData[3].fy2023),  // Op Ex Year'A'2
        'F23': Math.abs(incomeStatementData[3].fy2024),  // Op Ex Year'A'3
        
        // EBIT (calculated in template, but can set if needed)
        // EBITDA can be used as proxy for EBIT if D&A is small
        'C15': incomeStatementData[4].fy2022,  // EBIT Year'A'1 (using EBITDA as proxy)
        'D15': incomeStatementData[4].fy2023,  // EBIT Year'A'2
        'E15': incomeStatementData[4].fy2024,  // EBIT Year'A'3
        
        // NOPAT (Net Operating Profit After Tax) - using Net Income as proxy
        // 'C17': incomeStatementData[5].fy2022,  // NOPAT Year'A'1 (using Net Income)
        // 'D17': incomeStatementData[5].fy2023,  // NOPAT Year'A'2
        // 'E17': incomeStatementData[5].fy2024,  // NOPAT Year'A'3
        
        // (+) D&A (Depreciation & Amortization) - estimate from EBITDA - EBIT
        // Since we don't have D&A separately, we'll use a placeholder or calculate
        // D&A = EBITDA - EBIT, but we're using EBITDA as EBIT proxy, so D&A ≈ 0
        // You may want to add actual D&A data
        'D28': 0,  // D&A Year'A'1 (placeholder - add actual data)
        'E28': 0,  // D&A Year'A'2
        'F28': 0,  // D&A Year'A'3
        
        // (-) CapEx (Capital Expenditures) - using Investing Cash Flow as proxy
        'D29': Math.abs(cashFlowData[1].fy2022),  // CapEx Year'A'1 (Investing CF, make positive)
        'E29': Math.abs(cashFlowData[1].fy2023), // CapEx Year'A'2
        'F29': Math.abs(cashFlowData[1].fy2024), // CapEx Year'A'3
        
        // (-) Changes in WC (Working Capital) - calculate from balance sheet changes
        // WC Change = (Current Assets - Current Liabilities) change year-over-year
        // Simplified: using a placeholder - you may want to calculate this properly
        'D30': 0,  // Changes in WC Year'A'1 (placeholder - calculate from BS data)
        'E30': 0,  // Changes in WC Year'A'2
        'F30': 0,  // Changes in WC Year'A'3
        
        // Unlevered Free Cash Flow (calculated in template, but can set if available)
        'C21': cashFlowData[0].fy2022,  // UFCF Year'A'1 (using Operating CF as proxy)
        'D21': cashFlowData[0].fy2023,  // UFCF Year'A'2
        'E21': cashFlowData[0].fy2024,  // UFCF Year'A'3
        
        // ===== DCF SECTION =====
        // These are typically calculated by the template, but we can set if needed
        // Discount Period, Discount Factor, PV of UFCF are usually formulas
        
        // ===== TERMINAL VALUE SECTION =====
        // Terminal Value is typically calculated by the template
        
        // ===== ENTERPRISE VALUE SECTION =====
        // 'C30': enterpriseValue,  // Enterprise Value (adjust cell reference)
        
        // // (-) Net Debt
        // 'C31': netDebt,  // Net Debt (adjust cell reference)
        
        // // Equity Value
        // 'C32': equityValue,  // Equity Value (adjust cell reference)
        
        // // ===== PER SHARE PRICE TARGET SECTION =====
        // 'C35': sharesOutstanding,  // Shares Outstanding (adjust cell reference)
        // 'C36': dcfValuePerShare,   // Per Share Price Target (adjust cell reference)
        
        // // Implied Upside/Downside (calculated in template)
      };

      await downloadExcelFromTemplate(
        '/Templates/DCF_A_Template.xlsx',
        dataMap,
        'model-export'
      );
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export Excel file. Please check the console for details.');
    }
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
              <Button 
                size="sm" 
                className="bg-denari-3 hover:bg-denari-3/90"
                onClick={handleExport}
              >
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
