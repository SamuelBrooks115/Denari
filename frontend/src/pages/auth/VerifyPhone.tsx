import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export default function VerifyPhone() {
  const navigate = useNavigate();
  const location = useLocation();
  const identifier = location.state?.identifier || "(555) 123-4567";
  const [code, setCode] = useState("");

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate successful verification
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-hero">
      <Card className="w-full max-w-md shadow-elevated">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Verify Phone</CardTitle>
          <p className="text-center text-sm text-muted-foreground mt-2">
            We've sent a verification code to {identifier}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleNext} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="code">Verification Code</Label>
              <Input
                id="code"
                type="text"
                placeholder="Enter 6-digit code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                maxLength={6}
              />
            </div>

            <Button type="submit" className="w-full bg-primary hover:bg-primary/90">
              Next
            </Button>
          </form>

          <div className="text-center">
            <button
              onClick={() => navigate("/auth/recover-username")}
              className="text-sm text-primary hover:underline"
            >
              Try a Different Account
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
