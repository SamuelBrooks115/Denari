import { Hero } from "@/components/Hero";
import { SectionHeader } from "@/components/SectionHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { FileText, TrendingUp, DollarSign } from "lucide-react";

export default function ThreeStatement() {
  const statements = [
    {
      title: "Income Statement",
      icon: FileText,
      description:
        "The Income Statement shows a company's revenues, expenses, and profitability over a specific period. It's essential for understanding operational efficiency and profitability trends. This statement is the foundation for projecting future earnings and forms the basis of most valuation models.",
    },
    {
      title: "Balance Sheet",
      icon: TrendingUp,
      description:
        "The Balance Sheet provides a snapshot of a company's assets, liabilities, and equity at a specific point in time. It's crucial for assessing financial health, liquidity, and capital structure. Understanding balance sheet dynamics is key to modeling working capital and capital expenditure requirements.",
    },
    {
      title: "Cash Flow Statement",
      icon: DollarSign,
      description:
        "The Cash Flow Statement tracks the actual movement of cash through operating, investing, and financing activities. It's vital for understanding a company's ability to generate cash and fund operations. Free cash flow, derived from this statement, is the cornerstone of DCF valuation.",
    },
  ];

  return (
    <div className="min-h-screen">
      <Hero title="3 Statement Model" subtitle="Build integrated financial models with confidence" />

      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <SectionHeader
              title="The Foundation of Financial Modeling"
              subtitle="Understanding the three core financial statements"
            />

            <div className="mt-12 space-y-6">
              {statements.map((statement) => (
                <Card key={statement.title} className="shadow-soft">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-primary/10">
                        <statement.icon className="h-6 w-6 text-primary" />
                      </div>
                      <CardTitle className="text-2xl">{statement.title}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed">{statement.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="mt-12 bg-gradient-hero rounded-2xl p-8 text-white">
              <h3 className="text-2xl font-bold mb-4 text-center">Why It Is Important, Cool, and Functions</h3>
              <p className="text-denari-4 text-center mb-6 leading-relaxed">
                The integrated 3-statement model is the gold standard in financial analysis. Each statement connects to
                the others, creating a cohesive picture of a company's financial performance. Denari automates the
                linking logic, ensuring accuracy while saving hours of manual work. Our intelligent templates adapt to
                different industries and business models, making it easy to build comprehensive models that stand up to
                professional scrutiny.
              </p>
              <div className="text-center">
                <Link to="/login">
                  <Button size="lg" variant="secondary" className="bg-white text-denari-1 hover:bg-white/90">
                    Start Project
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
