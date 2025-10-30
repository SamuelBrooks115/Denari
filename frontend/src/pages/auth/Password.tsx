import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export default function Password() {
  const navigate = useNavigate();
  const location = useLocation();
  const identifier = location.state?.identifier || "first.last@email.com";
  const [password, setPassword] = useState("");

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate successful login
    localStorage.setItem("denari_logged_in", "true");
    navigate("/app/projects");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-hero">
      <Card className="w-full max-w-md shadow-elevated">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Enter Password</CardTitle>
          <p className="text-center text-sm text-muted-foreground mt-2">{identifier}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleNext} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button type="submit" className="w-full bg-primary hover:bg-primary/90">
              Next
            </Button>
          </form>

          <div className="text-center">
            <button className="text-sm text-primary hover:underline">
              Forgot your password?
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
