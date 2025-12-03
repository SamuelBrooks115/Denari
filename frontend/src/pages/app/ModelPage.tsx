import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Download, Settings, FileSpreadsheet, TrendingUp, TrendingDown, Plus } from "lucide-react";
import { useState } from "react";
import { downloadExcelFromTemplate } from "@/lib/downloadExcel";
import { Slider } from "@/components/ui/slider";
import { useNavigate } from "react-router-dom";

export default function ModelPage() {
  const navigate = useNavigate();
  
  // Shared CSS for financial tables to ensure divider alignment
  const financialTableStyle = `
    .financial-table {
      border-collapse: collapse;
      border-spacing: 0;
      table-layout: fixed;
      width: 100%;
    }
    .financial-table th:nth-child(4),
    .financial-table td:nth-child(4) {
      border-right: 2px solid #9ca3af;
    }
  `;

  // Mock financial data - Historical
  const incomeStatementData = [
    { item: "Revenue", fy2022: 125000, fy2023: 142000, fy2024: 165000 },
    { item: "Cost of Revenue", fy2022: -62500, fy2023: -69900, fy2024: -79200 },
    { item: "Gross Profit", fy2022: 62500, fy2023: 72100, fy2024: 85800 },
    { item: "Operating Expenses", fy2022: -37500, fy2023: -42600, fy2024: -49500 },
    { item: "EBITDA", fy2022: 25000, fy2023: 29500, fy2024: 36300 },
    { item: "Net Income", fy2022: 18750, fy2023: 22130, fy2024: 27225 },
  ];

  const balanceSheetData = [
    { item: "Cash & Equivalents", fy2022: 45000, fy2023: 52000, fy2024: 63000 },
    { item: "Accounts Receivable", fy2022: 22000, fy2023: 26000, fy2024: 31000 },
    { item: "Inventory", fy2022: 18000, fy2023: 21000, fy2024: 24000 },
    { item: "Total Assets", fy2022: 185000, fy2023: 220000, fy2024: 265000 },
    { item: "Total Liabilities", fy2022: 85000, fy2023: 95000, fy2024: 105000 },
    { item: "Stockholders' Equity", fy2022: 100000, fy2023: 125000, fy2024: 160000 },
  ];

  const cashFlowData = [
    { item: "Operating Cash Flow", fy2022: 22000, fy2023: 27000, fy2024: 34000 },
    { item: "Investing Cash Flow", fy2022: -8000, fy2023: -10000, fy2024: -12000 },
    { item: "Financing Cash Flow", fy2022: -5000, fy2023: -6000, fy2024: -7000 },
    { item: "Net Change in Cash", fy2022: 9000, fy2023: 11000, fy2024: 15000 },
  ];

  // Mock forecasted data - 5 years (2025-2029)
  const forecastedIncomeStatementData = [
    { item: "Revenue", fy2025: 192000, fy2026: 222000, fy2027: 255000, fy2028: 290000, fy2029: 330000 },
    { item: "Cost of Revenue", fy2025: -92160, fy2026: -106560, fy2027: -122400, fy2028: -139200, fy2029: -158400 },
    { item: "Gross Profit", fy2025: 99840, fy2026: 115440, fy2027: 132600, fy2028: 150800, fy2029: 171600 },
    { item: "Operating Expenses", fy2025: -57000, fy2026: -66000, fy2027: -76000, fy2028: -87000, fy2029: -99000 },
    { item: "EBITDA", fy2025: 42840, fy2026: 49440, fy2027: 56600, fy2028: 63800, fy2029: 72600 },
    { item: "Net Income", fy2025: 32130, fy2026: 37080, fy2027: 42450, fy2028: 47850, fy2029: 54450 },
  ];

  const forecastedBalanceSheetData = [
    { item: "Cash & Equivalents", fy2025: 78000, fy2026: 95000, fy2027: 115000, fy2028: 138000, fy2029: 165000 },
    { item: "Accounts Receivable", fy2025: 36000, fy2026: 42000, fy2027: 48000, fy2028: 55000, fy2029: 63000 },
    { item: "Inventory", fy2025: 28000, fy2026: 32000, fy2027: 37000, fy2028: 42000, fy2029: 48000 },
    { item: "Total Assets", fy2025: 320000, fy2026: 380000, fy2027: 450000, fy2028: 530000, fy2029: 625000 },
    { item: "Total Liabilities", fy2025: 120000, fy2026: 140000, fy2027: 165000, fy2028: 195000, fy2029: 230000 },
    { item: "Stockholders' Equity", fy2025: 200000, fy2026: 240000, fy2027: 285000, fy2028: 335000, fy2029: 395000 },
  ];

  const forecastedCashFlowData = [
    { item: "Operating Cash Flow", fy2025: 42000, fy2026: 48000, fy2027: 55000, fy2028: 63000, fy2029: 72000 },
    { item: "Investing Cash Flow", fy2025: -15000, fy2026: -18000, fy2027: -21000, fy2028: -25000, fy2029: -30000 },
    { item: "Financing Cash Flow", fy2025: -9000, fy2026: -10000, fy2027: -12000, fy2028: -14000, fy2029: -17000 },
    { item: "Net Change in Cash", fy2025: 18000, fy2026: 20000, fy2027: 22000, fy2028: 24000, fy2029: 25000 },
  ];

  const valuationData = [
    { metric: "DCF Value per Share", value: "$42.50", change: "+8.3%" },
    { metric: "P/E Ratio", value: "18.5x", change: "-2.1%" },
    { metric: "EV/EBITDA", value: "12.3x", change: "+1.8%" },
    { metric: "Price to Book", value: "2.8x", change: "+5.4%" },
  ];

  // DCF Projected Upside/Downside
  const currentPrice = 38.50;
  const dcfValuePerShare = 42.50;
  const projectedUpside = ((dcfValuePerShare - currentPrice) / currentPrice) * 100;
  const [valuationRange, setValuationRange] = useState([35.50, 49.50]);

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  const handleExport = async () => {
    try {
      const enterpriseValue = 425000000;
      const equityValue = 388000000;
      const dcfValuePerShare = 42.50;
      const netDebt = enterpriseValue - equityValue;
      const estimatedSharePrice = 150;
      const sharesOutstanding = Math.round(equityValue / estimatedSharePrice);

      const dataMap: Record<string, any> = {
        'B2': 'Apple Inc.',
        'J2': 'AAPL',
        'J5': new Date('2025-12-31'),
        'J6': balanceSheetData[0].fy2024,
        'J7': sharesOutstanding,
        'J8': estimatedSharePrice,
        'J9': equityValue,
        'J10': netDebt,
        'D17': incomeStatementData[0].fy2022,
        'E17': incomeStatementData[0].fy2023,
        'F17': incomeStatementData[0].fy2024,
        'D20': Math.abs(incomeStatementData[1].fy2022),
        'E20': Math.abs(incomeStatementData[1].fy2023),
        'F20': Math.abs(incomeStatementData[1].fy2024),
        'D23': Math.abs(incomeStatementData[3].fy2022),
        'E23': Math.abs(incomeStatementData[3].fy2023),
        'F23': Math.abs(incomeStatementData[3].fy2024),
        'C15': incomeStatementData[4].fy2022,
        'D15': incomeStatementData[4].fy2023,
        'E15': incomeStatementData[4].fy2024,
        'D28': 0,
        'E28': 0,
        'F28': 0,
        'D29': Math.abs(cashFlowData[1].fy2022),
        'E29': Math.abs(cashFlowData[1].fy2023),
        'F29': Math.abs(cashFlowData[1].fy2024),
        'D30': 0,
        'E30': 0,
        'F30': 0,
        'C21': cashFlowData[0].fy2022,
        'D21': cashFlowData[0].fy2023,
        'E21': cashFlowData[0].fy2024,
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
            <div className="inline-flex flex-col items-end gap-3">
              <div className="flex items-center gap-3">
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
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
              <Button 
                variant="outline" 
                size="sm"
                className="w-full"
                onClick={() => navigate("/app/projects/new")}
              >
                <Plus className="h-4 w-4 mr-2" />
                New Project
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">Last Updated: Jan 15, 2025</Badge>
            <Badge variant="outline" className="border-denari-5 text-denari-5">Status: Active</Badge>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="statements" className="space-y-6">
          <TabsList className="bg-denari-2/10">
            <TabsTrigger value="statements">Three-Statement Model</TabsTrigger>
            <TabsTrigger value="dcf">DCF Analysis</TabsTrigger>
            <TabsTrigger value="relative">Relative Valuation</TabsTrigger>
          </TabsList>

          {/* Three-Statement Model Tab - Combined */}
          <TabsContent value="statements" className="space-y-6">
            <style dangerouslySetInnerHTML={{ __html: financialTableStyle }} />
            {/* Income Statement Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5 text-denari-3" />
                  Income Statement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border overflow-hidden">
                  <div className="relative w-full overflow-auto">
                    <table className="financial-table w-full caption-bottom text-sm">
                      <colgroup>
                        <col style={{ width: '20%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                      </colgroup>
                      <thead className="[&_tr]:border-b">
                        <tr className="bg-denari-2/5 border-b">
                          <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground font-bold">Item</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2022</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2023</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2024</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2025</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2026</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2027</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2028</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2029</th>
                        </tr>
                      </thead>
                      <tbody className="[&_tr:last-child]:border-0">
                        {incomeStatementData.map((row, idx) => {
                          const forecastRow = forecastedIncomeStatementData[idx];
                          return (
                            <tr key={idx} className={`border-b transition-colors ${row.item === "Net Income" ? "bg-denari-5/5 font-semibold" : "hover:bg-muted/50"}`}>
                              <td className="p-4 align-middle font-medium">{row.item}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2022)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2023)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2024)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2025)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2026)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2027)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2028)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2029)}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Balance Sheet Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5 text-denari-3" />
                  Balance Sheet
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border overflow-hidden">
                  <div className="relative w-full overflow-auto">
                    <table className="financial-table w-full caption-bottom text-sm">
                      <colgroup>
                        <col style={{ width: '20%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                      </colgroup>
                      <thead className="[&_tr]:border-b">
                        <tr className="bg-denari-2/5 border-b">
                          <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground font-bold">Item</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2022</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2023</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2024</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2025</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2026</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2027</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2028</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2029</th>
                        </tr>
                      </thead>
                      <tbody className="[&_tr:last-child]:border-0">
                        {balanceSheetData.map((row, idx) => {
                          const forecastRow = forecastedBalanceSheetData[idx];
                          return (
                            <tr key={idx} className={`border-b transition-colors ${row.item === "Stockholders' Equity" ? "bg-denari-5/5 font-semibold" : "hover:bg-muted/50"}`}>
                              <td className="p-4 align-middle font-medium">{row.item}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2022)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2023)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2024)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2025)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2026)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2027)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2028)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2029)}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Cash Flow Statement Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5 text-denari-3" />
                  Cash Flow Statement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border overflow-hidden">
                  <div className="relative w-full overflow-auto">
                    <table className="financial-table w-full caption-bottom text-sm">
                      <colgroup>
                        <col style={{ width: '20%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                        <col style={{ width: '10%' }} />
                      </colgroup>
                      <thead className="[&_tr]:border-b">
                        <tr className="bg-denari-2/5 border-b">
                          <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground font-bold">Item</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2022</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2023</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2024</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2025</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2026</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2027</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2028</th>
                          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">FY 2029</th>
                        </tr>
                      </thead>
                      <tbody className="[&_tr:last-child]:border-0">
                        {cashFlowData.map((row, idx) => {
                          const forecastRow = forecastedCashFlowData[idx];
                          return (
                            <tr key={idx} className={`border-b transition-colors ${row.item === "Net Change in Cash" ? "bg-denari-5/5 font-semibold" : "hover:bg-muted/50"}`}>
                              <td className="p-4 align-middle font-medium">{row.item}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2022)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2023)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(row.fy2024)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2025)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2026)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2027)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2028)}</td>
                              <td className="p-4 align-middle text-right">${formatNumber(forecastRow.fy2029)}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* DCF Analysis Tab */}
          <TabsContent value="dcf" className="space-y-4">
            {/* Projected Upside/Downside at Top */}
            <Card>
              <CardHeader>
                <CardTitle>Projected Upside / Downside</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Current Price</p>
                      <p className="text-2xl font-bold">${currentPrice.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">DCF Value per Share</p>
                      <p className="text-2xl font-bold text-denari-1">${dcfValuePerShare.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Projected Upside</p>
                      <p className={`text-2xl font-bold ${projectedUpside >= 0 ? 'text-denari-5' : 'text-red-500'}`}>
                        {projectedUpside >= 0 ? '+' : ''}{projectedUpside.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  
                  {/* Valuation Range Slider */}
                  <div className="pt-4 border-t">
                    <p className="text-sm text-muted-foreground mb-4">Valuation Range</p>
                    <div className="space-y-4">
                      <Slider
                        value={valuationRange}
                        onValueChange={setValuationRange}
                        min={30}
                        max={55}
                        step={0.5}
                        className="w-full"
                      />
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">${valuationRange[0].toFixed(2)}</span>
                        <span className="text-sm font-medium">${valuationRange[1].toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Relative Valuation Tab */}
          <TabsContent value="relative" className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Left: Inputs */}
              <Card>
                <CardHeader>
                  <CardTitle>Inputs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">Select Competitors</p>
                      <p className="text-xs text-muted-foreground">Competitor selection interface will be implemented here</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Right: Valuation Average + Summary Panel */}
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Valuation Average</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {valuationData.slice(1, 4).map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">{item.metric}</span>
                          <span className="text-lg font-semibold">{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-muted-foreground">Implied Price Target</p>
                        <p className="text-2xl font-bold text-denari-1">$42.50</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Upside/Downside</p>
                        <p className="text-xl font-semibold text-denari-5">+10.4%</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
