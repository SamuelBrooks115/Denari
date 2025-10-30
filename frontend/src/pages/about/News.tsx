import { NewsCard } from "@/components/NewsCard";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Newspaper } from "lucide-react";

const newsArticles = [
  {
    slug: "denari-series-a",
    title: "Denari Raises $15M Series A to Accelerate Product Development",
    date: "October 15, 2025",
    excerpt:
      "We're excited to announce our Series A funding round led by premier venture capital firms. This investment will fuel product innovation and team expansion.",
  },
  {
    slug: "new-dcf-features",
    title: "Introducing Advanced DCF Sensitivity Analysis",
    date: "September 28, 2025",
    excerpt:
      "Our latest release includes powerful new sensitivity analysis tools that help you understand the impact of key assumptions on your valuations.",
  },
  {
    slug: "enterprise-launch",
    title: "Denari Enterprise: Built for Large Organizations",
    date: "August 12, 2025",
    excerpt:
      "We're launching Denari Enterprise with advanced security, governance, and collaboration features designed for institutional investors.",
  },
];

export default function News() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <div className="relative h-64 bg-gradient-hero overflow-hidden">
        <div className="absolute inset-0 bg-denari-1/50 backdrop-blur-sm" />
        <div className="relative h-full flex items-center justify-center">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-4 rounded-full bg-primary/20">
                <Newspaper className="h-12 w-12 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-white">News</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            {newsArticles.map((article) => (
              <NewsCard
                key={article.slug}
                {...article}
                onClick={() => navigate(`/about/news/${article.slug}`)}
              />
            ))}
          </div>

          <div className="text-center">
            <Button variant="outline" size="lg">
              See More News...
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
