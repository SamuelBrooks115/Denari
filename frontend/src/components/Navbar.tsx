import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { User, LogOut } from "lucide-react";
import { useState, useEffect } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const loggedIn = localStorage.getItem("denari_logged_in") === "true";
    setIsLoggedIn(loggedIn);
  }, [location]);

  const handleLogout = () => {
    localStorage.removeItem("denari_logged_in");
    setIsLoggedIn(false);
    navigate("/");
  };

  return (
    <nav className="sticky top-0 z-50 w-full bg-denari-1 border-b border-denari-2/30 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <Link to="/" className="text-2xl font-bold text-primary hover:text-primary/80 transition-colors">
            DENARI
          </Link>

          <div className="hidden md:flex items-center gap-6">
            <Link
              to="/"
              className="text-sm font-medium text-denari-4 hover:text-primary transition-colors"
            >
              Home
            </Link>
            {isLoggedIn && (
              <Link
                to="/app/model"
                className="text-sm font-medium text-denari-4 hover:text-primary transition-colors"
              >
                Model
              </Link>
            )}
            <Link
              to="/solutions"
              className="text-sm font-medium text-denari-4 hover:text-primary transition-colors"
            >
              Solutions
            </Link>
            <Link
              to="/industry"
              className="text-sm font-medium text-denari-4 hover:text-primary transition-colors"
            >
              Coming Soon
            </Link>
            <Link
              to="/about"
              className="text-sm font-medium text-denari-4 hover:text-primary transition-colors"
            >
              About Denari
            </Link>
          </div>

          <div className="flex items-center gap-4">
            {isLoggedIn ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                    <Avatar className="h-9 w-9">
                      <AvatarFallback className="bg-primary text-primary-foreground">U</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuItem asChild>
                    <Link to="/app/projects" className="flex items-center cursor-pointer">
                      <User className="mr-2 h-4 w-4" />
                      My Projects
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-destructive">
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Link to="/login">
                <Button size="sm" className="bg-primary hover:bg-primary/90">
                  Login
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
