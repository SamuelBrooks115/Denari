import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SignIn() {
  const navigate = useNavigate();
  const [emailOrPhone, setEmailOrPhone] = useState("");

  const handleContinue = (e: React.FormEvent) => {
    e.preventDefault();
    if (emailOrPhone) {
      // Simulate going to password screen
      navigate("/auth/password", { state: { identifier: emailOrPhone } });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-hero">
      <Card className="w-full max-w-md shadow-elevated">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Sign In to DENARI</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleContinue} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="emailOrPhone">Email or Phone</Label>
              <Input
                id="emailOrPhone"
                type="text"
                placeholder="your@email.com or (555) 123-4567"
                value={emailOrPhone}
                onChange={(e) => setEmailOrPhone(e.target.value)}
                required
              />
            </div>

            <Button type="submit" className="w-full bg-primary hover:bg-primary/90">
              Continue
            </Button>
          </form>

          <div className="space-y-3 text-center text-sm">
            <button
              onClick={() => navigate("/auth/recover-username")}
              className="text-primary hover:underline block w-full"
            >
              Forgot your username?
            </button>

            <div className="text-muted-foreground">
              Don't have an account?{" "}
              <button className="text-primary hover:underline">Sign Up</button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
