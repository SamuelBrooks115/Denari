import { NewsCard } from "@/components/NewsCard";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Newspaper } from "lucide-react";

const newsArticles = [
  {
    slug: "product-progress-update",
    title: "Product Progress Update",
    date: "October 15, 2025",
    excerpt:
      "Late nights and early mornings have become the norm as our team pushes forward to deliver an MVP for Hunter Sandidge. The dedication and passion driving this project is truly inspiring.",
  },
  {
    slug: "networking-ideas-gala",
    title: "Networking at Ideas Gala",
    date: "September 28, 2025",
    excerpt:
      "Our team had an incredible opportunity to connect with industry leaders and potential partners at the Ideas Gala, showcasing our product and building valuable relationships.",
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
          <div className="flex flex-wrap justify-center gap-6 mb-8">
            {newsArticles.map((article) => (
              <div key={article.slug} className="w-full md:w-[calc(50%-12px)] max-w-md">
                <NewsCard
                  {...article}
                  onClick={() => navigate(`/about/news/${article.slug}`)}
                />
              </div>
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
