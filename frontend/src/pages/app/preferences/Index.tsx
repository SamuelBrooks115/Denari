import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

export default function PreferencesIndex() {
  const handleSave = (section: string) => {
    toast.success(`${section} preferences saved successfully`);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">Preferences</h1>

        <Tabs defaultValue="excel" className="w-full">
          <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6">
            <TabsTrigger value="excel">Excel Output</TabsTrigger>
            <TabsTrigger value="dcf">DCF Defaults</TabsTrigger>
            <TabsTrigger value="three-statement">3 Statement</TabsTrigger>
            <TabsTrigger value="relative">Relative Val.</TabsTrigger>
            <TabsTrigger value="formatting">Formatting</TabsTrigger>
            <TabsTrigger value="colors">Colors</TabsTrigger>
          </TabsList>

          <TabsContent value="excel">
            <Card>
              <CardHeader>
                <CardTitle>Excel Output Preferences</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label>File Format</Label>
                  <RadioGroup defaultValue="xlsx">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="xlsx" id="xlsx" />
                      <Label htmlFor="xlsx">.xlsx</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="xlsm" id="xlsm" />
                      <Label htmlFor="xlsm">.xlsm</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="csv" id="csv" />
                      <Label htmlFor="csv">.csv</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Sheet Organization</Label>
                  <RadioGroup defaultValue="combined">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="combined" id="combined" />
                      <Label htmlFor="combined">Combined Output</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="separated" id="separated" />
                      <Label htmlFor="separated">Separated by Model</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Output Naming Convention</Label>
                  <RadioGroup defaultValue="ticker-model">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="ticker-model" id="ticker-model" />
                      <Label htmlFor="ticker-model">[Ticker]_Model</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="ticker-val-date" id="ticker-val-date" />
                      <Label htmlFor="ticker-val-date">[Ticker]_Valuation_Date</Label>
                    </div>
                  </RadioGroup>
                </div>

                <Button onClick={() => handleSave("Excel Output")} className="bg-primary hover:bg-primary/90">
                  SAVE
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="dcf">
            <Card>
              <CardHeader>
                <CardTitle>DCF Defaults</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label>Projection Periods</Label>
                  <RadioGroup defaultValue="5">
                    <div className="flex gap-4">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="3" id="proj-3" />
                        <Label htmlFor="proj-3">3 years</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="5" id="proj-5" />
                        <Label htmlFor="proj-5">5 years</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="7" id="proj-7" />
                        <Label htmlFor="proj-7">7 years</Label>
                      </div>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Historical Periods</Label>
                  <RadioGroup defaultValue="3">
                    <div className="flex gap-4">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="3" id="hist-3" />
                        <Label htmlFor="hist-3">3 years</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="5" id="hist-5" />
                        <Label htmlFor="hist-5">5 years</Label>
                      </div>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Cell References</Label>
                  <RadioGroup defaultValue="pull">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="pull" id="pull" />
                      <Label htmlFor="pull">Pull From 3 Statement</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="no-ref" id="no-ref" />
                      <Label htmlFor="no-ref">No Reference to I/S</Label>
                    </div>
                  </RadioGroup>
                </div>

                <Button onClick={() => handleSave("DCF Defaults")} className="bg-primary hover:bg-primary/90">
                  SAVE
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="three-statement">
            <Card>
              <CardHeader>
                <CardTitle>3 Statement Defaults</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label>Projection Periods</Label>
                  <RadioGroup defaultValue="5">
                    <div className="flex gap-4">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="3" id="stmt-proj-3" />
                        <Label htmlFor="stmt-proj-3">3 years</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="5" id="stmt-proj-5" />
                        <Label htmlFor="stmt-proj-5">5 years</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="7" id="stmt-proj-7" />
                        <Label htmlFor="stmt-proj-7">7 years</Label>
                      </div>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Historical Periods</Label>
                  <RadioGroup defaultValue="3">
                    <div className="flex gap-4">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="3" id="stmt-hist-3" />
                        <Label htmlFor="stmt-hist-3">3 years</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="5" id="stmt-hist-5" />
                        <Label htmlFor="stmt-hist-5">5 years</Label>
                      </div>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Tab Setup</Label>
                  <RadioGroup defaultValue="one-tab">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="one-tab" id="one-tab" />
                      <Label htmlFor="one-tab">One Tab</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="separate" id="separate" />
                      <Label htmlFor="separate">Separate Fin. Stmts.</Label>
                    </div>
                  </RadioGroup>
                </div>

                <Button onClick={() => handleSave("3 Statement Defaults")} className="bg-primary hover:bg-primary/90">
                  SAVE
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="relative">
            <Card>
              <CardHeader>
                <CardTitle>Relative Valuation Defaults</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label>Outlier Treatment</Label>
                  <RadioGroup defaultValue="trim">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="trim" id="trim" />
                      <Label htmlFor="trim">Trim Top/Bottom 5%</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="include-all" id="include-all" />
                      <Label htmlFor="include-all">Include All</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Peer Selection Method</Label>
                  <RadioGroup defaultValue="auto">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="auto" id="auto" />
                      <Label htmlFor="auto">Auto</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="manual" id="manual" />
                      <Label htmlFor="manual">Manual Entry</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Output Chart Type</Label>
                  <RadioGroup defaultValue="box">
                    <div className="flex gap-4">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="box" id="box" />
                        <Label htmlFor="box">Box</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="scatter" id="scatter" />
                        <Label htmlFor="scatter">Scatter</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="bar" id="bar" />
                        <Label htmlFor="bar">Bar</Label>
                      </div>
                    </div>
                  </RadioGroup>
                </div>

                <Button onClick={() => handleSave("Relative Valuation Defaults")} className="bg-primary hover:bg-primary/90">
                  SAVE
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="formatting">
            <Card>
              <CardHeader>
                <CardTitle>General Formatting</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label>Font Family</Label>
                  <Select defaultValue="arial">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="arial">Arial</SelectItem>
                      <SelectItem value="aptos">Aptos</SelectItem>
                      <SelectItem value="cambria">Cambria</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label>Font Size</Label>
                  <RadioGroup defaultValue="medium">
                    <div className="flex gap-4">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="small" id="small" />
                        <Label htmlFor="small">Small</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="medium" id="medium" />
                        <Label htmlFor="medium">Medium</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="large" id="large" />
                        <Label htmlFor="large">Large</Label>
                      </div>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Decimal Precision</Label>
                  <RadioGroup defaultValue="2">
                    <div className="flex gap-4">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="0" id="dec-0" />
                        <Label htmlFor="dec-0">0</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="1" id="dec-1" />
                        <Label htmlFor="dec-1">1</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="2" id="dec-2" />
                        <Label htmlFor="dec-2">2</Label>
                      </div>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Headers</Label>
                  <div className="flex gap-4">
                    <div className="flex items-center space-x-2">
                      <Switch id="bold" defaultChecked />
                      <Label htmlFor="bold">Bold</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch id="underlined" />
                      <Label htmlFor="underlined">Underlined</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch id="colored" />
                      <Label htmlFor="colored">Colored</Label>
                    </div>
                  </div>
                </div>

                <Button onClick={() => handleSave("General Formatting")} className="bg-primary hover:bg-primary/90">
                  SAVE
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="colors">
            <Card>
              <CardHeader>
                <CardTitle>Color Preferences</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label htmlFor="text-color">Text Color</Label>
                  <div className="flex gap-4 items-center">
                    <span className="text-sm text-muted-foreground">Black</span>
                    <Input id="text-color" type="text" defaultValue="#000000" className="max-w-xs" />
                  </div>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="negative-color">Negative Value Color</Label>
                  <div className="flex gap-4 items-center">
                    <span className="text-sm text-muted-foreground">Red</span>
                    <Input id="negative-color" type="text" defaultValue="#FF0000" className="max-w-xs" />
                  </div>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="assumption-color">Assumption Color</Label>
                  <div className="flex gap-4 items-center">
                    <span className="text-sm text-muted-foreground">Blue</span>
                    <Input id="assumption-color" type="text" defaultValue="#0000FF" className="max-w-xs" />
                  </div>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="formula-color">Formula Color</Label>
                  <div className="flex gap-4 items-center">
                    <span className="text-sm text-muted-foreground">Green</span>
                    <Input id="formula-color" type="text" defaultValue="#00FF00" className="max-w-xs" />
                  </div>
                </div>

                <Button onClick={() => handleSave("Color Preferences")} className="bg-primary hover:bg-primary/90">
                  SAVE
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
