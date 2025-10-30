import { Button } from "@/components/ui/button";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Calendar } from "lucide-react";

const articles: Record<string, { title: string; date: string; body: string }> = {
  "denari-series-a": {
    title: "Denari Raises $15M Series A to Accelerate Product Development",
    date: "October 15, 2025",
    body: `We're thrilled to announce that Denari has raised $15 million in Series A funding led by premier venture capital firms. This investment represents a major milestone in our journey to transform financial modeling for investment professionals.

The funding will be used to accelerate product development, expand our engineering team, and enhance our platform's capabilities. We're committed to building the most powerful and intuitive financial modeling tools available.

Our investors share our vision of democratizing professional-grade valuation tools. With their support, we'll continue to innovate and deliver features that make investment professionals more efficient and effective.

Thank you to our users, team members, and investors for believing in our mission. This is just the beginning.`,
  },
  "new-dcf-features": {
    title: "Introducing Advanced DCF Sensitivity Analysis",
    date: "September 28, 2025",
    body: `We're excited to launch our most requested feature: advanced sensitivity analysis for DCF valuations. This new capability allows you to quickly understand how changes in key assumptions impact your valuation results.

Key features include:
- Multi-variable sensitivity tables
- Tornado diagrams for identifying critical assumptions
- Scenario analysis with custom parameter ranges
- Visual representations of valuation ranges

Our sensitivity tools are designed to integrate seamlessly with your existing DCF models. Simply select your key assumptions, define ranges, and Denari generates comprehensive analysis automatically.

This feature is available now for all Venus plan subscribers and will be rolling out to Roma users in the coming weeks.`,
  },
  "enterprise-launch": {
    title: "Denari Enterprise: Built for Large Organizations",
    date: "August 12, 2025",
    body: `Today we're launching Denari Enterprise, a comprehensive solution designed specifically for large financial institutions and investment firms.

Denari Enterprise includes:
- Advanced security and compliance features
- Single sign-on (SSO) integration
- Centralized user and team management
- Custom approval workflows
- Dedicated support and training
- On-premises deployment options

Large organizations have unique requirements around security, governance, and collaboration. Denari Enterprise addresses these needs while maintaining the ease of use that makes Denari so powerful.

To learn more about Denari Enterprise, contact our sales team for a personalized demo.`,
  },
};

export default function NewsDetail() {
  const navigate = useNavigate();
  const { slug } = useParams<{ slug: string }>();
  const article = slug ? articles[slug] : null;

  if (!article) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Article not found</h1>
          <Button onClick={() => navigate("/about/news")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to All News
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="relative h-64 bg-gradient-hero overflow-hidden">
        <div className="absolute inset-0 bg-denari-1/50 backdrop-blur-sm" />
        <div className="relative h-full flex items-center justify-center px-4">
          <div className="text-center max-w-3xl">
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">{article.title}</h1>
            <div className="flex items-center justify-center gap-2 text-denari-4">
              <Calendar className="h-4 w-4" />
              {article.date}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto">
          <Button variant="ghost" onClick={() => navigate("/about/news")} className="mb-8">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to All News
          </Button>

          <div className="prose max-w-none">
            {article.body.split("\n\n").map((paragraph, index) => (
              <p key={index} className="text-lg text-muted-foreground leading-relaxed mb-4">
                {paragraph}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
