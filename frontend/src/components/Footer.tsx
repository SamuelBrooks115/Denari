import { Facebook, X, Linkedin, Mail, Phone } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Footer = () => {
  return (
    <footer className="bg-denari-2 text-white">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-lg font-bold mb-4">DENARI</h3>
            {/*<p className="text-sm text-denari-4">
              Professional financial modeling and valuation platform
            </p>*/}
          </div>

          <div>
            <h4 className="font-semibold mb-4">Learn More</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/industry" className="text-denari-4 hover:text-primary transition-colors">
                  Industry Overview
                </a>
              </li>
              <li>
                <a href="/solutions" className="text-denari-4 hover:text-primary transition-colors">
                  Solutions
                </a>
              </li>
              <li>
                <a href="/about" className="text-denari-4 hover:text-primary transition-colors">
                  About Us
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Contact</h4>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2 text-denari-4">
                <Mail className="h-4 w-4" />
                contactusdenari@gmail.com
              </li>
              <li className="flex items-center gap-2 text-denari-4">
                <Phone className="h-4 w-4" />
                +1 (920) 905-5240
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Follow Us</h4>
            <div className="flex gap-4">
              {/*<Button variant="ghost" size="icon" className="text-denari-4 hover:text-primary">
                <Facebook className="h-5 w-5" />
              </Button>*/}
              <Button variant="ghost" size="icon" className="text-denari-4 hover:text-primary">
                <X className="h-5 w-5" />
              </Button>
              <Button variant="ghost" size="icon" className="text-denari-4 hover:text-primary">
                <Linkedin className="h-5 w-5" />
              </Button>
            </div>
            <div className="mt-4">
              <Button variant="outline" size="sm" className="text-xs border-denari-4 text-denari-4 hover:bg-denari-4 hover:text-denari-1">
                Language: English
              </Button>
            </div>
          </div>
        </div>

        <div className="border-t border-denari-4/20 mt-8 pt-8 text-center text-sm text-denari-4">
          <p>&copy; {new Date().getFullYear()} Denari. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
