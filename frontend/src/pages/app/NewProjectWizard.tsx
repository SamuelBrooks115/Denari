import { useState, useEffect, useMemo } from "react";
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

import { useNavigate, useLocation } from "react-router-dom";
import { 
  convertWizardDataToProjectData, 
  saveProjectDataToFile, 
  saveProjectDataToLocalStorage,
  outputProjectDataJSON
} from "@/lib/saveProjectData";
import { fetchTenYearTreasuryRate } from "@/lib/fmpApi";

type WizardStep = "search" | "assumptions" | "review" | "generating";

// Type for ticker data from JSON
interface TickerData {
  symbol: string;
  companyName: string;
  tradingCurrency?: string;
  reportingCurrency?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function NewProjectWizard() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCompany, setSelectedCompany] = useState<{ name: string; ticker: string } | null>(null);
  const [open, setOpen] = useState(false);
  const [competitorSearchQuery, setCompetitorSearchQuery] = useState("");
  const [competitorOpen, setCompetitorOpen] = useState(false);
  const [allCompanies, setAllCompanies] = useState<TickerData[]>([]);
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(false);
  const [historicalData, setHistoricalData] = useState<{
    ticker: string;
    historicals: {
      revenueGrowth: number[];
      grossMargin: number[];
      operatingMargin: number[];
      taxRate: number[];
      depreciationPctPPE: number[];
      totalDebt: number[];
      inventory: number[];
      capexPctPPE: number[];
      capexPctRevenue: number[];
      shareRepurchases: number[];
      dividendsPctNI: number[];
      changeInWorkingCapital: number[];
    };
  } | null>(null);
  const [isLoadingHistorical, setIsLoadingHistorical] = useState(false);
  
  const [currentStep, setCurrentStep] = useState<WizardStep>("search");
  const [isSearching, setIsSearching] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedProjectId, setSavedProjectId] = useState<string | null>(null);
  const [wizardData, setWizardData] = useState({
    companyName: "",
    ticker: "",
    // Income Statement - 5 year forecast values
    revenueMethod: "stable" as "stable" | "step" | "manual",
    revenueStableValue: "",
    revenueStepValue: "",
    revenueValues: ["", "", "", "", ""],
    grossMarginMethod: "stable" as "stable" | "step" | "manual",
    grossMarginStableValue: "",
    grossMarginStepValue: "",
    grossMarginValues: ["", "", "", "", ""],
    operatingMarginMethod: "stable" as "stable" | "step" | "manual",
    operatingMarginStableValue: "",
    operatingMarginStepValue: "",
    operatingMarginValues: ["", "", "", "", ""],
    taxRateMethod: "stable" as "stable" | "step" | "manual",
    taxRateStableValue: "",
    taxRateStepValue: "",
    taxRateValues: ["", "", "", "", ""],
    interestRateOnDebtMethod: "stable" as "stable" | "step" | "manual",
    interestRateOnDebtStableValue: "",
    interestRateOnDebtStepValue: "",
    interestRateOnDebtValues: ["", "", "", "", ""],
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
    betaMethod: "calculate" as "calculate" | "manual",
    beta: "",
    betaCalculated: "",
    betaReference: "",
    betaYears: "3" as "1" | "3" | "5",
    betaBenchmark: "S&P 500" as "S&P 500" | "NASDAQ" | "Russell 2000" | "Dow Jones",
    marketRiskPremium: "4.33",
    riskFreeRate: "",
    terminalGrowthRate: "2.5",
    scenario: "bear" as "bear" | "bull",
    // Bear/Bull Scenario Assumptions
    bearRevenueMethod: "stable" as "stable" | "step" | "manual",
    bearRevenueStableValue: "",
    bearRevenueStepValue: "",
    bearRevenueValues: ["", "", "", "", ""],
    bearGrossMarginMethod: "stable" as "stable" | "step" | "manual",
    bearGrossMarginStableValue: "",
    bearGrossMarginStepValue: "",
    bearGrossMarginValues: ["", "", "", "", ""],
    bearOperatingMarginMethod: "stable" as "stable" | "step" | "manual",
    bearOperatingMarginStableValue: "",
    bearOperatingMarginStepValue: "",
    bearOperatingMarginValues: ["", "", "", "", ""],
    bearTaxRateMethod: "stable" as "stable" | "step" | "manual",
    bearTaxRateStableValue: "",
    bearTaxRateStepValue: "",
    bearTaxRateValues: ["", "", "", "", ""],
    bearDepreciationPercentPPE: "",
    bearCapexMethod: "revenue" as "revenue" | "depreciation",
    bearCapexValue: "",
    bearChangeInWCMethod: "stable" as "stable" | "step" | "manual",
    bearChangeInWCStableValue: "",
    bearChangeInWCStepValue: "",
    bearChangeInWCValues: ["", "", "", "", ""],
    bullRevenueMethod: "stable" as "stable" | "step" | "manual",
    bullRevenueStableValue: "",
    bullRevenueStepValue: "",
    bullRevenueValues: ["", "", "", "", ""],
    bullGrossMarginMethod: "stable" as "stable" | "step" | "manual",
    bullGrossMarginStableValue: "",
    bullGrossMarginStepValue: "",
    bullGrossMarginValues: ["", "", "", "", ""],
    bullOperatingMarginMethod: "stable" as "stable" | "step" | "manual",
    bullOperatingMarginStableValue: "",
    bullOperatingMarginStepValue: "",
    bullOperatingMarginValues: ["", "", "", "", ""],
    bullTaxRateMethod: "stable" as "stable" | "step" | "manual",
    bullTaxRateStableValue: "",
    bullTaxRateStepValue: "",
    bullTaxRateValues: ["", "", "", "", ""],
    bullDepreciationPercentPPE: "",
    bullCapexMethod: "revenue" as "revenue" | "depreciation",
    bullCapexValue: "",
    bullChangeInWCMethod: "stable" as "stable" | "step" | "manual",
    bullChangeInWCStableValue: "",
    bullChangeInWCStepValue: "",
    bullChangeInWCValues: ["", "", "", "", ""],
    // Relative Valuation
    competitors: [] as string[],
  });

  // Load available tickers from JSON file (non-blocking)
  useEffect(() => {
    let isMounted = true;
    let abortController: AbortController | null = null;
    
    const loadTickers = async () => {
      try {
        setIsLoadingCompanies(true);
        abortController = new AbortController();
        
        const response = await fetch("/available_tickers.json", {
          signal: abortController.signal,
        });
        
        if (!response.ok) {
          throw new Error(`Failed to load tickers: ${response.status}`);
        }
        
        const text = await response.text();
        let data: TickerData[] = [];
        
        try {
          data = JSON.parse(text);
        } catch (parseError) {
          console.error("Error parsing JSON:", parseError);
          throw new Error("Invalid JSON format");
        }
        
        if (!Array.isArray(data)) {
          console.warn("Ticker data is not an array");
          data = [];
        }
        
        if (isMounted) {
          setAllCompanies(data);
        }
      } catch (error: any) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error("Error loading tickers:", error);
        if (isMounted) {
          setAllCompanies([]);
        }
      } finally {
        if (isMounted) {
          setIsLoadingCompanies(false);
        }
      }
    };
    
    // Load after a small delay to not block initial render
    const timeoutId = setTimeout(() => {
      loadTickers();
    }, 100);
    
    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
      if (abortController) {
        abortController.abort();
      }
    };
  }, []);

  // Fetch 10-year treasury rate for Risk-Free Rate
  useEffect(() => {
    const loadTreasuryRate = async () => {
      const rate = await fetchTenYearTreasuryRate();
      
      if (rate !== null) {
        // Format to 2 decimal places and update wizard data
        const formattedRate = rate.toFixed(2);
        setWizardData(prev => ({
          ...prev,
          riskFreeRate: formattedRate
        }));
        toast.success(`Risk-Free Rate auto-populated: ${formattedRate}%`);
      } else {
        toast.error("Failed to auto-populate Risk-Free Rate. Please enter manually.");
      }
    };
    
    loadTreasuryRate();
  }, []);

  // Filter companies with ticker priority - searches entire dataset robustly
  const filteredCompanies = useMemo(() => {
    if (isLoadingCompanies || !allCompanies || allCompanies.length === 0) {
      return [];
    }
    
    // If no search query, return empty (will show "Start typing" message)
    if (!searchQuery.trim()) {
      return [];
    }
    
    const query = searchQuery.toLowerCase().trim();
    const queryWords = query.split(/\s+/).filter(w => w.length > 0);
    
    const exactTickerMatches: TickerData[] = [];
    const startsWithTickerMatches: TickerData[] = [];
    const includesTickerMatches: TickerData[] = [];
    const nameStartsWithMatches: TickerData[] = [];
    const nameWordMatches: TickerData[] = [];
    const nameIncludesMatches: TickerData[] = [];
    
    // Maximum results to collect
    const MAX_RESULTS = 100;
    
    // Search through ALL companies in the dataset
    for (let i = 0; i < allCompanies.length; i++) {
      const company = allCompanies[i];
      
      // Skip invalid entries
      if (!company || !company.symbol || !company.companyName) continue;
      
      const symbolLower = company.symbol.toLowerCase();
      const nameLower = company.companyName.toLowerCase();
      
      // TICKER MATCHES (highest priority)
      if (symbolLower === query) {
        exactTickerMatches.push(company);
      } else if (symbolLower.startsWith(query)) {
        startsWithTickerMatches.push(company);
      } else if (symbolLower.includes(query)) {
        includesTickerMatches.push(company);
      }
      
      // COMPANY NAME MATCHES (lower priority, but more sophisticated)
      else {
        // Check if name starts with query
        if (nameLower.startsWith(query)) {
          nameStartsWithMatches.push(company);
        }
        // Check if all query words appear in the company name (multi-word matching)
        else if (queryWords.length > 1 && queryWords.every(word => nameLower.includes(word))) {
          nameWordMatches.push(company);
        }
        // Check if name includes the query
        else if (nameLower.includes(query)) {
          nameIncludesMatches.push(company);
        }
      }
      
      // Early termination optimization: if we have enough high-priority matches and query is specific enough
      if (query.length >= 4) {
        const totalHighPriority = exactTickerMatches.length + startsWithTickerMatches.length + nameStartsWithMatches.length;
        if (totalHighPriority >= MAX_RESULTS) break;
      }
    }
    
    // Combine with priority: 
    // exact ticker > ticker starts with > ticker includes > 
    // name starts with > name word match > name includes
    const combined = [
      ...exactTickerMatches,
      ...startsWithTickerMatches,
      ...includesTickerMatches,
      ...nameStartsWithMatches,
      ...nameWordMatches,
      ...nameIncludesMatches
    ];
    
    // Return top 50 results
    return combined.slice(0, 50);
  }, [searchQuery, allCompanies, isLoadingCompanies]);

  // Show unavailable option if no matches found
  const showUnavailableOption = searchQuery.trim().length > 0 && filteredCompanies.length === 0 && !isLoadingCompanies;

  // Filter competitors with ticker priority (same logic as company search, but excludes selected company and already added competitors)
  const filteredCompetitors = useMemo(() => {
    if (isLoadingCompanies || !allCompanies || allCompanies.length === 0) {
      return [];
    }
    
    if (!competitorSearchQuery.trim()) {
      return [];
    }
    
    const query = competitorSearchQuery.toLowerCase().trim();
    const queryWords = query.split(/\s+/).filter(w => w.length > 0);
    
    const exactTickerMatches: TickerData[] = [];
    const startsWithTickerMatches: TickerData[] = [];
    const includesTickerMatches: TickerData[] = [];
    const nameStartsWithMatches: TickerData[] = [];
    const nameWordMatches: TickerData[] = [];
    const nameIncludesMatches: TickerData[] = [];
    
    const MAX_RESULTS = 100;
    const excludedTickers = new Set([
      wizardData.ticker, // Exclude the selected company
      ...wizardData.competitors // Exclude already added competitors
    ]);
    
    // Search through ALL companies in the dataset
    for (let i = 0; i < allCompanies.length; i++) {
      const company = allCompanies[i];
      
      // Skip invalid entries or excluded companies
      if (!company || !company.symbol || !company.companyName || excludedTickers.has(company.symbol)) {
        continue;
      }
      
      const symbolLower = company.symbol.toLowerCase();
      const nameLower = company.companyName.toLowerCase();
      
      // TICKER MATCHES (highest priority)
      if (symbolLower === query) {
        exactTickerMatches.push(company);
      } else if (symbolLower.startsWith(query)) {
        startsWithTickerMatches.push(company);
      } else if (symbolLower.includes(query)) {
        includesTickerMatches.push(company);
      }
      // COMPANY NAME MATCHES (lower priority, but more sophisticated)
      else {
        // Check if name starts with query
        if (nameLower.startsWith(query)) {
          nameStartsWithMatches.push(company);
        }
        // Check if all query words appear in the company name (multi-word matching)
        else if (queryWords.length > 1 && queryWords.every(word => nameLower.includes(word))) {
          nameWordMatches.push(company);
        }
        // Check if name includes the query
        else if (nameLower.includes(query)) {
          nameIncludesMatches.push(company);
        }
      }
      
      // Early termination optimization: if we have enough high-priority matches and query is specific enough
      if (query.length >= 4) {
        const totalHighPriority = exactTickerMatches.length + startsWithTickerMatches.length + nameStartsWithMatches.length;
        if (totalHighPriority >= MAX_RESULTS) break;
      }
    }
    
    // Combine with priority: 
    // exact ticker > ticker starts with > ticker includes > 
    // name starts with > name word match > name includes
    const combined = [
      ...exactTickerMatches,
      ...startsWithTickerMatches,
      ...includesTickerMatches,
      ...nameStartsWithMatches,
      ...nameWordMatches,
      ...nameIncludesMatches
    ];
    
    // Return top 50 results
    return combined.slice(0, 50);
  }, [competitorSearchQuery, allCompanies, isLoadingCompanies, wizardData.ticker, wizardData.competitors]);

  // Show unavailable option for competitors if no matches found
  const showUnavailableCompetitorOption = competitorSearchQuery.trim().length > 0 && filteredCompetitors.length === 0 && !isLoadingCompanies;

  // Check for pre-filled company from navigation state (e.g., from Industry Screener)
  useEffect(() => {
    const state = (location as any).state as { company?: { name: string; ticker: string } } | null | undefined;
    if (state?.company) {
      const { name, ticker } = state.company;
      
      // Scroll to top when navigating with pre-filled company
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }, 100);
      
      // Wait for companies to load, then find and select the company
      const selectCompany = () => {
        if (allCompanies.length > 0 && ticker && ticker !== "N/A") {
          // Find the company in the list by ticker (case-insensitive)
          const foundCompany = allCompanies.find(
            (c) => c.symbol.toUpperCase() === ticker.toUpperCase()
          );
          
          if (foundCompany) {
            // Company found in list - select it properly using handleCompanySelect
            // This will set the company name in the input field and close the popover
            handleCompanySelect(foundCompany);
          } else {
            // Company not found in list - set manually with the provided name
            setSelectedCompany({ name, ticker });
            setWizardData((prev) => ({ ...prev, companyName: name, ticker: ticker }));
            setSearchQuery(name); // Set the company name in the input field
            setOpen(false); // Close the popover
            fetchHistoricalData(ticker);
          }
        } else if (ticker && ticker !== "N/A") {
          // Companies not loaded yet, set manually and fetch historical data
          setSelectedCompany({ name, ticker });
          setWizardData((prev) => ({ ...prev, companyName: name, ticker: ticker }));
          setSearchQuery(name); // Set the company name in the input field
          setOpen(false); // Close the popover
          fetchHistoricalData(ticker);
        } else {
          // Invalid ticker, just set the name
          setSelectedCompany({ name, ticker });
          setWizardData((prev) => ({ ...prev, companyName: name, ticker: ticker }));
          setSearchQuery(name); // Set the company name in the input field
          setOpen(false); // Close the popover
        }
        
        // Clear the state to prevent re-applying on re-renders
        window.history.replaceState({}, document.title);
      };
      
      // If companies are already loaded, select immediately
      // Otherwise, wait for them to load (with retries)
      if (allCompanies.length > 0) {
        selectCompany();
      } else {
        // Wait for companies to load, with multiple retries
        let retries = 0;
        const maxRetries = 10; // Try for up to 5 seconds (10 * 500ms)
        
        const trySelect = () => {
          if (allCompanies.length > 0) {
            selectCompany();
          } else if (retries < maxRetries) {
            retries++;
            setTimeout(trySelect, 500);
          } else {
            // Companies still not loaded after max retries, set manually
            selectCompany();
          }
        };
        
        const timeoutId = setTimeout(trySelect, 500);
        
        return () => clearTimeout(timeoutId);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [(location as any).state, allCompanies]);

  const handleCompanySelect = (company: TickerData | "unavailable") => {
    if (company === "unavailable") {
      const unavailableCompany = {
        name: searchQuery.trim() || "Unavailable Company",
        ticker: "N/A",
      };
      setSelectedCompany(unavailableCompany);
      setWizardData({ ...wizardData, companyName: unavailableCompany.name, ticker: unavailableCompany.ticker });
      setSearchQuery(unavailableCompany.name);
    } else {
      const selected = { name: company.companyName, ticker: company.symbol };
      setSelectedCompany(selected);
      setWizardData({ ...wizardData, companyName: selected.name, ticker: selected.ticker });
      setSearchQuery(selected.name);
      
      // Fetch historical data when a valid ticker is selected
      fetchHistoricalData(selected.ticker);
    }
    setOpen(false);
  };

  // Fetch historical financial data from backend when ticker is selected
  const fetchHistoricalData = async (ticker: string) => {
    // Skip if ticker is "N/A" or unavailable
    if (!ticker || ticker === "N/A" || ticker === "unavailable") {
      setHistoricalData(null);
      return;
    }

    setIsLoadingHistorical(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/historical/metrics`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticker: ticker,
          limit: 40,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch historical data: ${response.status}`);
      }

      const data = await response.json();
      setHistoricalData(data);
      console.log("Historical data fetched successfully:", data);
    } catch (error) {
      console.error("Error fetching historical data:", error);
      // Don't show error toast - this is background data, not critical for user flow
      setHistoricalData(null);
    } finally {
      setIsLoadingHistorical(false);
    }
  };

  const handleFinish = async () => {
    if (!selectedCompany) {
      toast.error("Please select a company");
      return;
    }
    
    // Validate that 4 competitors are selected
    if (!wizardData.competitors || wizardData.competitors.length < 4) {
      toast.error(`Please select exactly 4 competitors. Currently selected: ${wizardData.competitors?.length || 0}`);
      return;
    }
    
    if (wizardData.competitors.length > 4) {
      toast.error(`Please select exactly 4 competitors. Currently selected: ${wizardData.competitors.length}`);
      return;
    }
    
    setIsSaving(true);
    try {
      // Debug: Log wizardData before conversion
      console.log("\n=== WIZARD DATA BEFORE CONVERSION ===");
      console.log("Tax Rate Step Value:", wizardData.taxRateStepValue, "| Type:", typeof wizardData.taxRateStepValue);
      console.log("Tax Rate Stable Value:", wizardData.taxRateStableValue, "| Type:", typeof wizardData.taxRateStableValue);
      console.log("Tax Rate Values:", wizardData.taxRateValues);
      console.log("Debt Change Step Value:", wizardData.debtChangeStepValue, "| Type:", typeof wizardData.debtChangeStepValue);
      console.log("Debt Change Stable Value:", wizardData.debtChangeStableValue, "| Type:", typeof wizardData.debtChangeStableValue);
      console.log("Debt Change Values:", wizardData.debtChangeValues);
      console.log("Change in WC Step Value:", wizardData.changeInWCStepValue, "| Type:", typeof wizardData.changeInWCStepValue);
      console.log("Change in WC Stable Value:", wizardData.changeInWCStableValue, "| Type:", typeof wizardData.changeInWCStableValue);
      console.log("Change in WC Values:", wizardData.changeInWCValues);
      console.log("Inventory Stable Value:", wizardData.inventoryStableValue, "| Type:", typeof wizardData.inventoryStableValue);
      console.log("Inventory Step Value:", wizardData.inventoryStepValue, "| Type:", typeof wizardData.inventoryStepValue);
      console.log("CAPEX Value:", wizardData.capexValue, "| Type:", typeof wizardData.capexValue);
      console.log("Share Repurchases:", wizardData.shareRepurchases, "| Type:", typeof wizardData.shareRepurchases);
      console.log("=== END WIZARD DATA ===\n");
      
      // Convert wizard data to structured project data
      const projectData = convertWizardDataToProjectData(
        wizardData,
        selectedCompany.name,
        selectedCompany.ticker,
        historicalData // Pass historical data to be included in project JSON
      );
      
      // Output JSON to console for verification
      outputProjectDataJSON(projectData);
      
      // Save to localStorage (for frontend access)
      saveProjectDataToLocalStorage(projectData);
      
      // Download JSON file for backend testing
      saveProjectDataToFile(projectData);
      
      // Save to backend API
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(projectData),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      const saveResult = await response.json();
      setSavedProjectId(projectData.projectId);
      
      toast.success("Project saved successfully! You can now generate the valuation.");
    } catch (error) {
      console.error("Error saving project:", error);
      toast.error(`Failed to save project: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateValuation = async () => {
    if (!savedProjectId) {
      toast.error("Please save the project first before generating valuation.");
      return;
    }
    
    setIsGenerating(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/valuation/export`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ projectId: savedProjectId }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      // Get the filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = `${selectedCompany?.ticker || "valuation"}_valuation.xlsx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("Valuation Excel file downloaded successfully!");
      
      // Redirect to My Projects after a short delay
      setTimeout(() => {
        navigate("/app/projects");
      }, 1000);
    } catch (error) {
      console.error("Error generating valuation:", error);
      toast.error(`Failed to generate valuation: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsGenerating(false);
    }
  };


  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  // Helper function to ensure a value is always negative (for CAPEX and Share Repurchases)
  // If user enters -1, it stays -1. If user enters 1, it becomes -1.
  const ensureNegative = (value: string): string => {
    if (!value || value === "") return "";
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return value;
    // If already negative, keep it as is. Otherwise, make it negative.
    if (numValue < 0) {
      return value; // Already negative, return as-is
    }
    // Positive value, make it negative
    return `-${Math.abs(numValue)}`;
  };

  // Helper function to format display value (show absolute value for input, but indicate it's negative)
  const formatNegativeDisplay = (value: string): string => {
    if (!value || value === "") return "";
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return value;
    // Display absolute value (user enters positive, we store as negative)
    return Math.abs(numValue).toString();
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
                  <Popover open={open} onOpenChange={setOpen} modal={false}>
                    <PopoverTrigger asChild>
                      <div className="w-full">
                        <Input
                          id="search"
                          placeholder="e.g., AAPL or Apple Inc."
                          value={searchQuery}
                          onChange={(e) => {
                            setSearchQuery(e.target.value);
                            if (!open) setOpen(true);
                          }}
                          onFocus={(e) => {
                            e.stopPropagation();
                            setOpen(true);
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpen(true);
                          }}
                          onMouseDown={(e) => {
                            e.stopPropagation();
                            // Small delay to ensure the click event fires first
                            setTimeout(() => setOpen(true), 0);
                          }}
                        />
                      </div>
                    </PopoverTrigger>
                    <PopoverContent 
                      className="w-[400px] p-0" 
                      align="start"
                      onOpenAutoFocus={(e) => {
                        // Prevent auto-focus on the CommandInput when popover opens
                        e.preventDefault();
                      }}
                      onInteractOutside={(e) => {
                        // Prevent closing when clicking the input field
                        const target = e.target as HTMLElement;
                        const inputElement = document.getElementById("search");
                        const popoverContent = target.closest('[role="dialog"]');
                        
                        if (inputElement && (inputElement.contains(target) || target === inputElement)) {
                          e.preventDefault();
                          return;
                        }
                        
                        // Also prevent closing if clicking inside the popover
                        if (popoverContent) {
                          e.preventDefault();
                          return;
                        }
                      }}
                    >
                      <Command shouldFilter={false}>
                        <CommandInput 
                          placeholder="Search companies..." 
                          value={searchQuery}
                          onValueChange={(value) => {
                            setSearchQuery(value);
                            setOpen(true);
                          }}
                        />
                        <CommandList className="max-h-[300px]">
                          {isLoadingCompanies ? (
                            <div className="py-6 text-center text-sm text-muted-foreground">
                              Loading companies...
                            </div>
                          ) : searchQuery.trim().length === 0 ? (
                            <CommandEmpty>
                              Start typing to search for a company or ticker...
                            </CommandEmpty>
                          ) : filteredCompanies.length > 0 ? (
                            <CommandGroup>
                              {filteredCompanies.map((company) => (
                                <CommandItem
                                  key={company.symbol}
                                  value={`${company.companyName} ${company.symbol}`}
                                  onSelect={() => handleCompanySelect(company)}
                                >
                                  <div className="flex flex-col">
                                    <span className="font-medium">{company.companyName}</span>
                                    <span className="text-xs text-muted-foreground">{company.symbol}</span>
                                  </div>
                                </CommandItem>
                              ))}
                            </CommandGroup>
                          ) : showUnavailableOption ? (
                            <CommandGroup>
                              <CommandItem
                                value="unavailable-company"
                                onSelect={() => handleCompanySelect("unavailable")}
                                className="text-destructive"
                              >
                                <div className="flex flex-col">
                                  <span className="font-medium">Unavailable Company</span>
                                  <span className="text-xs text-muted-foreground">Not in our database: {searchQuery.trim()}</span>
                                </div>
                              </CommandItem>
                            </CommandGroup>
                          ) : (
                            <CommandEmpty>
                              No companies found.
                            </CommandEmpty>
                          )}
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
                          setHistoricalData(null);
                          setWizardData({ ...wizardData, companyName: "", ticker: "" });
                        }}
                      >
                        <X className="h-4 w-4" />
                        </Button>
                      </div>
                  
                  {/* Historical Data Preview Table */}
                  {isLoadingHistorical && (
                    <div className="mt-4 p-4 text-center text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin inline-block mr-2" />
                      Loading historical financial data...
                    </div>
                  )}
                  
                  {historicalData && historicalData.historicals && !isLoadingHistorical && (
                    <div className="mt-4">
                      <h3 className="text-sm font-semibold mb-3">Historical Financial Metrics Preview</h3>
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="min-w-[120px]">Metric</TableHead>
                              {(() => {
                                const currentYear = new Date().getFullYear();
                                return [currentYear - 2, currentYear - 1, currentYear].map((year) => (
                                  <TableHead key={year} className="text-right">{year}</TableHead>
                                ));
                              })()}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            <TableRow>
                              <TableCell className="font-medium">Revenue Growth</TableCell>
                              {historicalData.historicals.revenueGrowth.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {(value * 100).toFixed(2)}%
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Gross Margin</TableCell>
                              {historicalData.historicals.grossMargin.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {(value * 100).toFixed(2)}%
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Operating Margin</TableCell>
                              {historicalData.historicals.operatingMargin.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {(value * 100).toFixed(2)}%
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Tax Rate</TableCell>
                              {historicalData.historicals.taxRate.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {(value * 100).toFixed(2)}%
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Depreciation % of PPE</TableCell>
                              {historicalData.historicals.depreciationPctPPE.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {(value * 100).toFixed(2)}%
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Total Debt</TableCell>
                              {historicalData.historicals.totalDebt.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {formatNumber(value)}
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Inventory</TableCell>
                              {historicalData.historicals.inventory.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {formatNumber(value)}
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">CAPEX % of PPE</TableCell>
                              {historicalData.historicals.capexPctPPE.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {(value * 100).toFixed(2)}%
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">CAPEX % of Revenue</TableCell>
                              {historicalData.historicals.capexPctRevenue.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {(value * 100).toFixed(2)}%
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Share Repurchases</TableCell>
                              {historicalData.historicals.shareRepurchases.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {formatNumber(value)}
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Dividends % of NI</TableCell>
                              {historicalData.historicals.dividendsPctNI.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {(value * 100).toFixed(2)}%
                                </TableCell>
                              ))}
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium">Change in Working Capital</TableCell>
                              {historicalData.historicals.changeInWorkingCapital.slice(0, 3).map((value, index) => (
                                <TableCell key={index} className="text-right">
                                  {formatNumber(value)}
                                </TableCell>
                              ))}
                            </TableRow>
                          </TableBody>
                        </Table>
                  </div>
                      <p className="text-xs text-muted-foreground mt-2">
                        Showing last 3 years. Full historical data will be saved in project JSON.
                      </p>
                    </div>
                  )}
                </div>
              )}
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
                            onWheel={(e) => e.currentTarget.blur()}
                            className="flex-1"
                          />
                        )}
                        {wizardData.revenueMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.revenueStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, revenueStepValue: e.target.value })}
                            onWheel={(e) => e.currentTarget.blur()}
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
                                onWheel={(e) => e.currentTarget.blur()}
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
                                placeholder={`Y${year + 1} - %`}
                                value={wizardData.grossMarginValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.grossMarginValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, grossMarginValues: newValues });
                                }}
                                onWheel={(e) => e.currentTarget.blur()}
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
                            onWheel={(e) => e.currentTarget.blur()}
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
                          value={wizardData.interestRateOnDebtMethod}
                          onValueChange={(value) => setWizardData({ ...wizardData, interestRateOnDebtMethod: value as "stable" | "step" | "manual" })}
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
                        {wizardData.interestRateOnDebtMethod === "stable" && (
                          <Input
                            type="number"
                            placeholder="%"
                            value={wizardData.interestRateOnDebtStableValue}
                            onChange={(e) => setWizardData({ ...wizardData, interestRateOnDebtStableValue: e.target.value })}
                            onWheel={(e) => e.currentTarget.blur()}
                            className="flex-1"
                          />
                        )}
                        {wizardData.interestRateOnDebtMethod === "step" && (
                          <Input
                            type="number"
                            placeholder="Step rate %"
                            value={wizardData.interestRateOnDebtStepValue}
                            onChange={(e) => setWizardData({ ...wizardData, interestRateOnDebtStepValue: e.target.value })}
                            onWheel={(e) => e.currentTarget.blur()}
                            className="flex-1"
                          />
                        )}
                        {wizardData.interestRateOnDebtMethod === "manual" && (
                          <div className="flex gap-2 flex-1">
                            {[0, 1, 2, 3, 4].map((year) => (
                              <Input
                                key={year}
                                type="number"
                                placeholder={`Y${year + 1} - %`}
                                value={wizardData.interestRateOnDebtValues[year]}
                                onChange={(e) => {
                                  const newValues = [...wizardData.interestRateOnDebtValues];
                                  newValues[year] = e.target.value;
                                  setWizardData({ ...wizardData, interestRateOnDebtValues: newValues });
                                }}
                                onWheel={(e) => e.currentTarget.blur()}
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
                      <Label>Long Term Debt Change</Label>
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
                        <div className="flex items-center gap-1 flex-1">
                          <span className="text-sm font-medium text-muted-foreground">-</span>
                          <Input
                            type="number"
                            placeholder="Percentage"
                            value={formatNegativeDisplay(wizardData.capexValue)}
                            onWheel={(e) => e.currentTarget.blur()}
                            onChange={(e) => {
                              const negativeValue = ensureNegative(e.target.value);
                              setWizardData({ ...wizardData, capexValue: negativeValue });
                            }}
                            className="flex-1"
                          />
                            </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="repurchases">Share Repurchases</Label>
                      <div className="flex items-center gap-1">
                        <span className="text-sm font-medium text-muted-foreground">-</span>
                        <Input
                          id="repurchases"
                          type="number"
                          placeholder="e.g., 5000"
                          value={formatNegativeDisplay(wizardData.shareRepurchases)}
                          onWheel={(e) => e.currentTarget.blur()}
                          onChange={(e) => {
                            const negativeValue = ensureNegative(e.target.value);
                            setWizardData({ ...wizardData, shareRepurchases: negativeValue });
                          }}
                          className="flex-1"
                        />
                </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="dividend">Dividend as % of Net Income</Label>
                      <Input
                        id="dividend"
                        type="number"
                        placeholder="e.g., 25"
                        value={wizardData.dividendPercentNI}
                        onChange={(e) => setWizardData({ ...wizardData, dividendPercentNI: e.target.value })}
                        onWheel={(e) => e.currentTarget.blur()}
                      />
                    </div>

                  </div>
                </div>

                {/* DCF Inputs */}
                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>DCF Model Assumptions</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    {/* Base Assumptions */}
                    <div className="space-y-4 pt-4 border-t">
                      <h4 className="font-semibold text-lg">Base Assumptions</h4>
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
                            onWheel={(e) => e.currentTarget.blur()}
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
                        placeholder="4.33"
                        value={wizardData.marketRiskPremium}
                        onChange={(e) => setWizardData({ ...wizardData, marketRiskPremium: e.target.value })}
                        onWheel={(e) => e.currentTarget.blur()}
                      />
                      <p className="text-xs text-muted-foreground">Default: 4.33%</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="rfr">Risk-Free Rate</Label>
                      <Input
                        id="rfr"
                        type="number"
                        placeholder="2.5"
                        value={wizardData.riskFreeRate}
                        onChange={(e) => setWizardData({ ...wizardData, riskFreeRate: e.target.value })}
                        onWheel={(e) => e.currentTarget.blur()}
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
                        onWheel={(e) => e.currentTarget.blur()}
                      />
                </div>
                    </div>

                    <div className="space-y-4">
                      {/* Bear Scenario Assumptions */}
                      <div className="space-y-4 pt-4 border-t">
                        <h4 className="font-semibold text-lg">Bear Scenario Assumptions</h4>
                          
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
                            <Label htmlFor="depreciation-bear-scenario">Depreciation as % of Revenue</Label>
                            <Input
                              id="depreciation-bear-scenario"
                              type="number"
                              placeholder="e.g., 10"
                              value={wizardData.bearDepreciationPercentPPE}
                              onChange={(e) => setWizardData({ ...wizardData, bearDepreciationPercentPPE: e.target.value })}
                              onWheel={(e) => e.currentTarget.blur()}
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
                              <div className="flex items-center gap-1 flex-1">
                                <span className="text-sm font-medium text-muted-foreground">-</span>
                                <Input
                                  type="number"
                                  placeholder="Percentage"
                                  value={formatNegativeDisplay(wizardData.bearCapexValue)}
                                  onChange={(e) => {
                                    const negativeValue = ensureNegative(e.target.value);
                                    setWizardData({ ...wizardData, bearCapexValue: negativeValue });
                                  }}
                                  className="flex-1"
                                />
                              </div>
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

                      {/* Bull Scenario Assumptions */}
                      <div className="space-y-4 pt-4 border-t mt-6">
                        <h4 className="font-semibold text-lg">Bull Scenario Assumptions</h4>
                        
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
                            <Label htmlFor="depreciation-bull-scenario">Depreciation as % of Revenue</Label>
                            <Input
                              id="depreciation-bull-scenario"
                              type="number"
                              placeholder="e.g., 10"
                              value={wizardData.bullDepreciationPercentPPE}
                              onChange={(e) => setWizardData({ ...wizardData, bullDepreciationPercentPPE: e.target.value })}
                              onWheel={(e) => e.currentTarget.blur()}
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
                              <div className="flex items-center gap-1 flex-1">
                                <span className="text-sm font-medium text-muted-foreground">-</span>
                                <Input
                                  type="number"
                                  placeholder="Percentage"
                                  value={formatNegativeDisplay(wizardData.bullCapexValue)}
                                  onChange={(e) => {
                                    const negativeValue = ensureNegative(e.target.value);
                                    setWizardData({ ...wizardData, bullCapexValue: negativeValue });
                                  }}
                                  className="flex-1"
                                />
                              </div>
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
                    </div>
                  </div>
                </div>

                <div className="space-y-6 mb-8">
                  <CardHeader className="p-0">
                    <CardTitle>Relative Valuation Assumptions</CardTitle>
                  </CardHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Select Competitors</Label>
                      <div className="space-y-2">
                        <Popover open={competitorOpen} onOpenChange={setCompetitorOpen} modal={false}>
                          <PopoverTrigger asChild>
                            <div className="w-full">
                              <Input
                                id="competitor-search"
                                placeholder="e.g., MSFT or Microsoft"
                                value={competitorSearchQuery}
                                onChange={(e) => {
                                  setCompetitorSearchQuery(e.target.value);
                                  if (!competitorOpen) setCompetitorOpen(true);
                                }}
                                onFocus={(e) => {
                                  e.stopPropagation();
                                  setCompetitorOpen(true);
                                }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setCompetitorOpen(true);
                                }}
                                onMouseDown={(e) => {
                                  e.stopPropagation();
                                  setTimeout(() => setCompetitorOpen(true), 0);
                                }}
                              />
                            </div>
                          </PopoverTrigger>
                          <PopoverContent 
                            className="w-[400px] p-0" 
                            align="start"
                            onOpenAutoFocus={(e) => {
                              e.preventDefault();
                            }}
                            onInteractOutside={(e) => {
                              const target = e.target as HTMLElement;
                              const inputElement = document.getElementById("competitor-search");
                              const popoverContent = target.closest('[role="dialog"]');
                              
                              if (inputElement && (inputElement.contains(target) || target === inputElement)) {
                                e.preventDefault();
                                return;
                              }
                              
                              if (popoverContent) {
                                e.preventDefault();
                                return;
                              }
                            }}
                          >
                            <Command shouldFilter={false}>
                              <CommandInput 
                                placeholder="Search competitors..." 
                                value={competitorSearchQuery}
                                onValueChange={(value) => {
                                  setCompetitorSearchQuery(value);
                                  setCompetitorOpen(true);
                                }}
                              />
                              <CommandList className="max-h-[300px]">
                                {isLoadingCompanies ? (
                                  <div className="py-6 text-center text-sm text-muted-foreground">
                                    Loading companies...
                                  </div>
                                ) : competitorSearchQuery.trim().length === 0 ? (
                                  <CommandEmpty>
                                    Start typing to search for a competitor...
                                  </CommandEmpty>
                                ) : filteredCompetitors.length > 0 ? (
                                  <CommandGroup>
                                    {filteredCompetitors.map((company) => (
                                      <CommandItem
                                        key={company.symbol}
                                        value={`${company.companyName} ${company.symbol}`}
                                        onSelect={() => {
                                          if (!wizardData.competitors.includes(company.symbol)) {
                                            setWizardData({
                                              ...wizardData,
                                              competitors: [...wizardData.competitors, company.symbol],
                                            });
                                            setCompetitorSearchQuery("");
                                            setCompetitorOpen(false);
                                          }
                                        }}
                                      >
                                        <div className="flex flex-col">
                                          <span className="font-medium">{company.companyName}</span>
                                          <span className="text-xs text-muted-foreground">{company.symbol}</span>
                                        </div>
                                      </CommandItem>
                                    ))}
                                  </CommandGroup>
                                ) : (
                                  <CommandEmpty>
                                    No competitors found.
                                  </CommandEmpty>
                                )}
                              </CommandList>
                            </Command>
                          </PopoverContent>
                        </Popover>
                        <div className="flex flex-wrap gap-2">
                          {wizardData.competitors.map((ticker) => {
                            const company = allCompanies.find(c => c.symbol === ticker);
                            return (
                              <Badge key={ticker} variant="secondary" className="flex items-center gap-2">
                                {company?.companyName || ticker}
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
                        Please select exactly 4 competitors. For each competitor, we will pull or compute: Market Cap, Revenue, EBITDA, Earnings, EV, Price/Sales, P/E, EV/EBITDA, EV/Revenue
                      </p>
                      {wizardData.competitors.length > 0 && (
                        <p className={`text-xs ${wizardData.competitors.length === 4 ? 'text-green-600' : 'text-orange-600'}`}>
                          {wizardData.competitors.length} of 4 competitors selected
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Save and Generate Buttons */}
                <div className="flex justify-end gap-4 pt-6 border-t">
                  <Button 
                    onClick={handleFinish} 
                    className="bg-secondary hover:bg-secondary/90" 
                    size="lg"
                    disabled={
                      isSaving || 
                      !wizardData.competitors || 
                      wizardData.competitors.length !== 4 ||
                      savedProjectId !== null
                    }
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : savedProjectId ? (
                      <>
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Saved
                      </>
                    ) : (
                      "Save Project"
                    )}
                  </Button>
                  <Button 
                    onClick={handleGenerateValuation} 
                    className="bg-primary hover:bg-primary/90" 
                    size="lg"
                    disabled={
                      !savedProjectId || 
                      isGenerating ||
                      !wizardData.competitors || 
                      wizardData.competitors.length !== 4
                    }
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      "Generate Valuation"
                    )}
                  </Button>
                </div>
                {wizardData.competitors && wizardData.competitors.length !== 4 && (
                  <p className="text-sm text-orange-600 text-right mt-2">
                    Please select exactly 4 competitors to continue
                  </p>
                )}
                {!savedProjectId && wizardData.competitors && wizardData.competitors.length === 4 && (
                  <p className="text-sm text-muted-foreground text-right mt-2">
                    Click "Save Project" first, then "Generate Valuation"
                  </p>
                )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

