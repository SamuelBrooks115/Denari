import { Button } from "@/components/ui/button";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Calendar } from "lucide-react";

const articles: Record<string, { title: string; date: string; body: string }> = {
  "product-progress-update": {
    title: "Product Progress Update",
    date: "October 15, 2025",
    body: `The past few weeks have been a whirlwind of late-night coding sessions, early morning standups, and countless cups of coffee as our team works tirelessly to deliver an MVP for Hunter Sandidge. The energy in the office (and virtual workspaces) has been electric, with team members staying up well past midnight to ensure every feature meets our high standards.

Working closely with Hunter Sandidge has been an incredible experience. His vision and feedback have pushed us to think differently about how financial modeling tools should work. The iterative process of building, testing, and refining has taught us invaluable lessons about product development and user-centric design.

Despite the long hours, the team's morale remains high. There's something special about being part of a startup that's genuinely passionate about solving real problems. Every bug fix, every new feature, every breakthrough moment brings us closer to delivering something we're truly proud of.

We're making significant progress on core features including the DCF modeling capabilities, industry screener functionality, and the intuitive project creation workflow. The MVP is taking shape, and we can't wait to share it with Hunter and the broader community.

The journey of building an MVP is never easy, but it's moments like these—when the team comes together, pushes through challenges, and creates something meaningful—that remind us why we started Denari in the first place.`,
  },
  "networking-ideas-gala": {
    title: "Networking at Ideas Gala",
    date: "September 28, 2025",
    body: `Last week, our team had the incredible opportunity to attend the Ideas Gala, an annual networking event that brings together entrepreneurs, investors, and innovators from across the tech and finance industries. It was an evening filled with meaningful conversations, new connections, and exciting opportunities to showcase Denari.

The event provided the perfect platform to introduce our product to potential users and partners. We had numerous engaging discussions with investment professionals who were genuinely interested in how Denari could streamline their valuation workflows. The feedback was overwhelmingly positive, with many expressing excitement about our approach to making financial modeling more accessible and intuitive.

One of the highlights of the evening was connecting with several early-stage investors who were intrigued by our vision. We shared our journey, discussed the challenges we've overcome, and outlined our roadmap for the future. These conversations reinforced our belief that we're building something that addresses a real need in the market.

Beyond the business opportunities, the Ideas Gala was a chance to learn from other founders and entrepreneurs. Hearing their stories of perseverance, innovation, and growth was both inspiring and humbling. It reminded us that we're part of a larger community of builders who are passionate about creating solutions that make a difference.

We left the event with a stack of business cards, several follow-up meetings scheduled, and a renewed sense of excitement about the path ahead. Networking events like the Ideas Gala are crucial for startups—they're where relationships are built, partnerships are formed, and opportunities are discovered. We're grateful for the experience and look forward to continuing these conversations as we grow.`,
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
