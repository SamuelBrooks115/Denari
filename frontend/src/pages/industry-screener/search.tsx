import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { fetchSectors, fetchIndustries, fetchIndustryScreener, CompanyResult } from "@/lib/api/industryScreener";
import { Loader2, ArrowUpDown, ArrowUp, ArrowDown, ExternalLink } from "lucide-react";

export default function IndustryScreenerSearch() {
  const navigate = useNavigate();
  const [sectors, setSectors] = useState<string[]>([]);
  const [industries, setIndustries] = useState<string[]>([]);
  const [selectedSector, setSelectedSector] = useState<string | undefined>(undefined);
  const [selectedIndustry, setSelectedIndustry] = useState<string | undefined>(undefined);
  const [minCap, setMinCap] = useState<string>("");
  const [maxCap, setMaxCap] = useState<string>("");
  const [page, setPage] = useState<number>(0);
  const [pageSize, setPageSize] = useState<number>(50);
  const [results, setResults] = useState<CompanyResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"name" | "marketCap" | null>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc" | null>(null);
  const [selectedCompany, setSelectedCompany] = useState<CompanyResult | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [companyDescription, setCompanyDescription] = useState<string | null>(null);
  const [loadingDescription, setLoadingDescription] = useState(false);

  // Load sectors on mount
  useEffect(() => {
    const loadSectors = async () => {
      try {
        setLoadingMeta(true);
        const sectorsData = await fetchSectors();
        setSectors(sectorsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load sectors");
      } finally {
        setLoadingMeta(false);
      }
    };
    loadSectors();
  }, []);

  // Load industries when sector changes
  useEffect(() => {
    const loadIndustries = async () => {
      try {
        setLoadingMeta(true);
        // Clear selected industry when sector changes
        setSelectedIndustry(undefined);
        const industriesData = await fetchIndustries(selectedSector);
        setIndustries(industriesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load industries");
      } finally {
        setLoadingMeta(false);
      }
    };
    loadIndustries();
  }, [selectedSector]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Validate market cap range
      const minCapNum = minCap ? parseFloat(minCap) : undefined;
      const maxCapNum = maxCap ? parseFloat(maxCap) : undefined;
      
      if (minCapNum !== undefined && maxCapNum !== undefined && minCapNum > maxCapNum) {
        setError("Minimum market cap cannot be greater than maximum market cap");
        setLoading(false);
        return;
      }
      
      // Validate page size
      if (pageSize < 1 || pageSize > 200) {
        setError("Page size must be between 1 and 200");
        setLoading(false);
        return;
      }
      
      const response = await fetchIndustryScreener({
        sector: selectedSector || undefined,
        industry: selectedIndustry || undefined,
        minCap: minCapNum ? Math.floor(minCapNum) : undefined,
        maxCap: maxCapNum ? Math.floor(maxCapNum) : undefined,
        page: page,
        pageSize: pageSize,
      });
      
      setResults(response.results);
      // Reset sorting when new results are loaded
      setSortBy(null);
      setSortOrder(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch screener results");
      setResults([]);
      setSortBy(null);
      setSortOrder(null);
    } finally {
      setLoading(false);
    }
  };

  const formatMarketCap = (cap: number): string => {
    if (cap >= 1_000_000_000_000) {
      return `$${(cap / 1_000_000_000_000).toFixed(2)}T`;
    } else if (cap >= 1_000_000_000) {
      return `$${(cap / 1_000_000_000).toFixed(2)}B`;
    } else if (cap >= 1_000_000) {
      return `$${(cap / 1_000_000).toFixed(2)}M`;
    } else {
      return `$${cap.toLocaleString()}`;
    }
  };

  // Handle sorting - cycles through: default → asc → desc → default
  const handleSort = (field: "name" | "marketCap") => {
    if (sortBy !== field) {
      // New field: start with ascending
      setSortBy(field);
      setSortOrder("asc");
    } else {
      // Same field: cycle through states
      if (sortOrder === "asc") {
        setSortOrder("desc");
      } else if (sortOrder === "desc") {
        // desc → reset to default
        setSortBy(null);
        setSortOrder(null);
      } else {
        // null (default) → asc
        setSortOrder("asc");
      }
    }
  };

  // Get sorted results
  const getSortedResults = (): CompanyResult[] => {
    if (!sortBy || !sortOrder) {
      return results; // Default: no sorting
    }

    const sorted = [...results];
    
    if (sortBy === "name") {
      sorted.sort((a, b) => {
        const nameA = a.name.toLowerCase();
        const nameB = b.name.toLowerCase();
        if (sortOrder === "asc") {
          return nameA.localeCompare(nameB);
        } else {
          return nameB.localeCompare(nameA);
        }
      });
    } else if (sortBy === "marketCap") {
      sorted.sort((a, b) => {
        if (sortOrder === "asc") {
          return a.marketCap - b.marketCap;
        } else {
          return b.marketCap - a.marketCap;
        }
      });
    }
    
    return sorted;
  };

  // Get sort icon for a field
  const getSortIcon = (field: "name" | "marketCap") => {
    if (sortBy !== field) {
      return <ArrowUpDown className="ml-2 h-4 w-4 text-muted-foreground" />;
    }
    if (sortOrder === "asc") {
      return <ArrowUp className="ml-2 h-4 w-4" />;
    } else if (sortOrder === "desc") {
      return <ArrowDown className="ml-2 h-4 w-4" />;
    }
    return <ArrowUpDown className="ml-2 h-4 w-4 text-muted-foreground" />;
  };

  const handleClear = () => {
    setSelectedSector(undefined);
    setSelectedIndustry(undefined);
    setMinCap("");
    setMaxCap("");
    setPage(0);
    setResults([]);
    setError(null);
    setSortBy(null);
    setSortOrder(null);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Industry Screener</CardTitle>
            <CardDescription>
              Filter companies by sector, industry, and market cap
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                <div className="space-y-2">
                  <Label htmlFor="sector">Sector</Label>
                  {loadingMeta ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <Select
                      value={selectedSector || "all"}
                      onValueChange={(value) => {
                        setSelectedSector(value === "all" ? undefined : value);
                        setSelectedIndustry(undefined); // Reset industry when sector changes
                      }}
                    >
                      <SelectTrigger id="sector">
                        <SelectValue placeholder="All Sectors" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Sectors</SelectItem>
                        {sectors.map((sector) => (
                          <SelectItem key={sector} value={sector}>
                            {sector}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="industry">Industry</Label>
                  {loadingMeta ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <Select
                      value={selectedIndustry || "all"}
                      onValueChange={(value) => {
                        setSelectedIndustry(value === "all" ? undefined : value);
                      }}
                    >
                      <SelectTrigger id="industry">
                        <SelectValue placeholder="All Industries" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Industries</SelectItem>
                        {industries.map((industry) => (
                          <SelectItem key={industry} value={industry}>
                            {industry}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="minCap">Minimum Market Cap</Label>
                  <Input
                    id="minCap"
                    type="number"
                    placeholder="e.g., 1000000000"
                    value={minCap}
                    onChange={(e) => setMinCap(e.target.value)}
                    onWheel={(e) => e.currentTarget.blur()}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxCap">Maximum Market Cap</Label>
                  <Input
                    id="maxCap"
                    type="number"
                    placeholder="e.g., 1000000000000"
                    value={maxCap}
                    onChange={(e) => setMaxCap(e.target.value)}
                    onWheel={(e) => e.currentTarget.blur()}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="page">Page</Label>
                  <Input
                    id="page"
                    type="number"
                    min="0"
                    placeholder="0"
                    value={page}
                    onChange={(e) => setPage(parseInt(e.target.value) || 0)}
                    onWheel={(e) => e.currentTarget.blur()}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pageSize">Page Size (max 200)</Label>
                  <Input
                    id="pageSize"
                    type="number"
                    min="1"
                    max="200"
                    placeholder="50"
                    value={pageSize}
                    onChange={(e) => {
                      const value = parseInt(e.target.value) || 50;
                      setPageSize(Math.min(200, Math.max(1, value)));
                    }}
                    onWheel={(e) => e.currentTarget.blur()}
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="submit" disabled={loading || loadingMeta}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Running Screener...
                    </>
                  ) : (
                    "Run Screener"
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClear}
                  disabled={loading}
                >
                  Clear
                </Button>
              </div>

              {error && (
                <Alert variant="destructive" className="mt-4">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </form>
          </CardContent>
        </Card>

        {loading && results.length === 0 && (
          <Card>
            <CardContent className="py-8">
              <div className="space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </CardContent>
          </Card>
        )}

        {!loading && results.length === 0 && !error && (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No companies match these filters. Try adjusting your criteria and click "Run Screener".
            </CardContent>
          </Card>
        )}

        {results.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Results ({results.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>
                        <button
                          type="button"
                          onClick={() => handleSort("name")}
                          className="flex items-center hover:text-primary transition-colors"
                        >
                          Company Name
                          {getSortIcon("name")}
                        </button>
                      </TableHead>
                      <TableHead>Ticker</TableHead>
                      <TableHead>Sector</TableHead>
                      <TableHead>Industry</TableHead>
                      <TableHead className="text-right">
                        <button
                          type="button"
                          onClick={() => handleSort("marketCap")}
                          className="flex items-center justify-end ml-auto hover:text-primary transition-colors"
                        >
                          Market Cap
                          {getSortIcon("marketCap")}
                        </button>
                      </TableHead>
                      <TableHead className="text-right">Stock Price</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {getSortedResults().map((company) => (
                      <TableRow key={company.symbol}>
                        <TableCell className="font-medium">
                          <button
                            type="button"
                            onClick={async () => {
                              setSelectedCompany(company);
                              setDialogOpen(true);
                              setCompanyDescription(null);
                              setLoadingDescription(true);
                              
                              // Fetch company profile with description
                              try {
                                const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
                                const response = await fetch(
                                  `${apiUrl}/api/v1/industry-screener/company-profile/${company.symbol}`
                                );
                                if (response.ok) {
                                  const profile = await response.json();
                                  setCompanyDescription(profile.description || null);
                                }
                              } catch (error) {
                                console.error("Error fetching company description:", error);
                              } finally {
                                setLoadingDescription(false);
                              }
                            }}
                            className="text-primary hover:underline cursor-pointer"
                          >
                            {company.name}
                          </button>
                        </TableCell>
                        <TableCell className="font-mono font-semibold">{company.symbol}</TableCell>
                        <TableCell>{company.sector}</TableCell>
                        <TableCell>{company.industry}</TableCell>
                        <TableCell className="text-right">{formatMarketCap(company.marketCap)}</TableCell>
                        <TableCell className="text-right">
                          {company.price !== undefined && company.price !== null
                            ? `$${company.price.toFixed(2)}`
                            : <span className="text-muted-foreground">—</span>}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Company Details Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-2xl">{selectedCompany?.name}</DialogTitle>
              <DialogDescription className="text-base">
                {selectedCompany?.symbol} • {selectedCompany?.sector} • {selectedCompany?.industry}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <h4 className="font-semibold mb-2">Company Description</h4>
                {loadingDescription ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <p className="text-sm text-muted-foreground">Loading description...</p>
                  </div>
                ) : companyDescription ? (
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {companyDescription}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground italic">
                    No description available for this company.
                  </p>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Market Cap</p>
                  <p className="text-lg font-semibold">
                    {selectedCompany ? formatMarketCap(selectedCompany.marketCap) : "—"}
                  </p>
                </div>
                {selectedCompany?.price !== undefined && selectedCompany?.price !== null && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Stock Price</p>
                    <p className="text-lg font-semibold">${selectedCompany.price.toFixed(2)}</p>
                  </div>
                )}
              </div>
              
              {selectedCompany?.website && (
                <div className="pt-4 border-t">
                  <a
                    href={selectedCompany.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline flex items-center gap-1"
                  >
                    Visit Website <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDialogOpen(false)}
              >
                Close
              </Button>
              <Button
                onClick={() => {
                  if (selectedCompany) {
                    setDialogOpen(false);
                    navigate("/app/projects/new", {
                      state: {
                        company: {
                          name: selectedCompany.name,
                          ticker: selectedCompany.symbol,
                        },
                      },
                    });
                    // Scroll to top after navigation
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }
                }}
              >
                Value This Company
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

