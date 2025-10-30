import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function RecoverUsername() {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    // Determine if email or phone
    const isEmail = identifier.includes("@");
    navigate(isEmail ? "/auth/verify-email" : "/auth/verify-phone", {
      state: { identifier },
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-hero">
      <Card className="w-full max-w-md shadow-elevated">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Recover Username</CardTitle>
          <p className="text-center text-sm text-muted-foreground mt-2">
            Enter your email or phone number to receive a verification code
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleNext} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="identifier">Email or Phone</Label>
              <Input
                id="identifier"
                type="text"
                placeholder="your@email.com or (555) 123-4567"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
              />
            </div>

            <Button type="submit" className="w-full bg-primary hover:bg-primary/90">
              Next
            </Button>
          </form>

          <div className="text-center">
            <button
              onClick={() => navigate("/login")}
              className="text-sm text-primary hover:underline"
            >
              Back to Sign In
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
