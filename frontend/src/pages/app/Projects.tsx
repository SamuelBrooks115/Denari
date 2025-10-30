import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { Plus, FolderOpen, Clock } from "lucide-react";

export default function Projects() {
  const recentProjects = [
    { id: 1, name: "AAPL Valuation Model", updated: "2 hours ago", type: "3-Statement + DCF" },
    { id: 2, name: "MSFT Relative Valuation", updated: "1 day ago", type: "Relative Valuation" },
    { id: 3, name: "TSLA Industry Analysis", updated: "3 days ago", type: "Industry Overview" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">My Projects</h1>
          <Link to="/app/projects/new">
            <Button size="lg" className="gap-2 bg-primary hover:bg-primary/90">
              <Plus className="h-5 w-5" />
              Create a New Project
            </Button>
          </Link>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {recentProjects.map((project) => (
            <Link key={project.id} to="/app/model">
              <Card className="shadow-soft hover:shadow-elevated transition-all hover:scale-[1.02]">
                <CardHeader>
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <FolderOpen className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{project.name}</CardTitle>
                      <p className="text-xs text-muted-foreground mt-1">{project.type}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    Updated {project.updated}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        <div className="text-center">
          <Button variant="outline">Older Projects...</Button>
        </div>
      </div>
    </div>
  );
}
