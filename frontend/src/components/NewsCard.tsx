import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar } from "lucide-react";

interface NewsCardProps {
  title: string;
  date: string;
  excerpt: string;
  slug: string;
  onClick: () => void;
}

export const NewsCard = ({ title, date, excerpt, onClick }: NewsCardProps) => {
  return (
    <Card
      className="shadow-soft hover:shadow-elevated transition-all cursor-pointer hover:scale-[1.02]"
      onClick={onClick}
    >
      <div className="h-48 bg-gradient-card rounded-t-2xl" />
      <CardHeader>
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <Calendar className="h-4 w-4" />
          {date}
        </div>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">{excerpt}</p>
      </CardContent>
    </Card>
  );
};
