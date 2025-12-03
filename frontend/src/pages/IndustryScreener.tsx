import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { fetchSectors, fetchIndustries, fetchIndustryScreener, CompanyResult } from "@/lib/api/industryScreener";

const IndustryScreener = () => {
  const [sectors, setSectors] = useState<string[]>([]);
  const [industries, setIndustries] = useState<string[]>([]);
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);
  const [minCapBillions, setMinCapBillions] = useState<string>("");
  const [maxCapBillions, setMaxCapBillions] = useState<string>("");
  const [results, setResults] = useState<CompanyResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize] = useState(50);
  const [hasMore, setHasMore] = useState(false);

  // Load sectors and industries on mount
  useEffect(() => {
    const loadMeta = async () => {
      try {
        setLoadingMeta(true);
        const [sectorsData, industriesData] = await Promise.all([
          fetchSectors(),
          fetchIndustries(),
        ]);
        setSectors(sectorsData);
        setIndustries(industriesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load sectors and industries");
      } finally {
        setLoadingMeta(false);
      }
    };
    loadMeta();
  }, []);

  const handleSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Convert billions to dollars
      const minCap = minCapBillions ? parseFloat(minCapBillions) * 1_000_000_000 : undefined;
      const maxCap = maxCapBillions ? parseFloat(maxCapBillions) * 1_000_000_000 : undefined;
      
      // Validate market cap range
      if (minCap !== undefined && maxCap !== undefined && minCap > maxCap) {
        setError("Minimum market cap cannot be greater than maximum market cap");
        setLoading(false);
        return;
      }
      
      const response = await fetchIndustryScreener({
        sector: selectedSector || undefined,
        industry: selectedIndustry || undefined,
        minCap: minCap ? Math.floor(minCap) : undefined,
        maxCap: maxCap ? Math.floor(maxCap) : undefined,
        page: page,
        pageSize: pageSize,
      });
      
      setResults(response.results);
      setHasMore(response.results.length === pageSize);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch screener results");
      setResults([]);
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

  const truncateDescription = (desc: string | undefined, maxLength: number = 150): string => {
    if (!desc) return "";
    if (desc.length <= maxLength) return desc;
    return desc.substring(0, maxLength) + "...";
  };

  const handleNextPage = () => {
    setPage(page + 1);
  };

  const handlePrevPage = () => {
    if (page > 0) {
      setPage(page - 1);
    }
  };

  // Trigger search when page changes (only if we already have a search in progress)
  useEffect(() => {
    // Only auto-search if we're on a page > 0 and we have previous results
    // This prevents infinite loops on initial load
    if (page > 0 && results.length > 0) {
      handleSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Industry Screener</CardTitle>
            <CardDescription>
              Filter companies by sector, industry, and market capitalization
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Sector</label>
                {loadingMeta ? (
                  <Skeleton className="h-10 w-full" />
                ) : (
                  <Select
                    value={selectedSector || ""}
                    onValueChange={(value) => {
                      setSelectedSector(value || null);
                      setSelectedIndustry(null); // Reset industry when sector changes
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All Sectors" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Sectors</SelectItem>
                      {sectors.map((sector) => (
                        <SelectItem key={sector} value={sector}>
                          {sector}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Industry</label>
                {loadingMeta ? (
                  <Skeleton className="h-10 w-full" />
                ) : (
                  <Select
                    value={selectedIndustry || ""}
                    onValueChange={(value) => setSelectedIndustry(value || null)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All Industries" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Industries</SelectItem>
                      {industries.map((industry) => (
                        <SelectItem key={industry} value={industry}>
                          {industry}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Min Market Cap (Billions)</label>
                <Input
                  type="number"
                  placeholder="e.g., 10"
                  value={minCapBillions}
                  onChange={(e) => setMinCapBillions(e.target.value)}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Max Market Cap (Billions)</label>
                <Input
                  type="number"
                  placeholder="e.g., 1000"
                  value={maxCapBillions}
                  onChange={(e) => setMaxCapBillions(e.target.value)}
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleSearch} disabled={loading || loadingMeta}>
                {loading ? "Searching..." : "Search"}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setSelectedSector(null);
                  setSelectedIndustry(null);
                  setMinCapBillions("");
                  setMaxCapBillions("");
                  setResults([]);
                  setPage(0);
                  setError(null);
                }}
              >
                Clear
              </Button>
            </div>

            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

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
                      <TableHead>Logo</TableHead>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Sector</TableHead>
                      <TableHead>Industry</TableHead>
                      <TableHead>Market Cap</TableHead>
                      <TableHead>Website</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {results.map((company) => (
                      <TableRow key={company.symbol}>
                        <TableCell>
                          {company.logoUrl ? (
                            <img
                              src={company.logoUrl}
                              alt={`${company.name} logo`}
                              className="w-10 h-10 object-contain"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = "none";
                              }}
                            />
                          ) : (
                            <div className="w-10 h-10 bg-gray-200 rounded flex items-center justify-center text-xs">
                              {company.symbol.substring(0, 2)}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="font-mono font-semibold">{company.symbol}</TableCell>
                        <TableCell className="font-medium">{company.name}</TableCell>
                        <TableCell>{company.sector}</TableCell>
                        <TableCell>{company.industry}</TableCell>
                        <TableCell>{formatMarketCap(company.marketCap)}</TableCell>
                        <TableCell>
                          {company.website ? (
                            <a
                              href={company.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline"
                            >
                              Visit
                            </a>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="max-w-md">
                          {company.description ? (
                            <span className="text-sm text-gray-600">
                              {truncateDescription(company.description)}
                            </span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex justify-between items-center mt-4">
                <div className="text-sm text-gray-600">
                  Page {page + 1}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={handlePrevPage}
                    disabled={page === 0 || loading}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleNextPage}
                    disabled={!hasMore || loading}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

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
            <CardContent className="py-8 text-center text-gray-500">
              No results. Try adjusting your filters and click Search.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default IndustryScreener;

