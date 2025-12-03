import { Card, CardContent } from "@/components/ui/card";
import { User } from "lucide-react";

interface TeamCardProps {
  name: string;
  role: string;
  bio: string;
  image?: string;
  imagePosition?: string;
  onClick: () => void;
}

export const TeamCard = ({ name, role, image, imagePosition = '50% 25%', onClick }: TeamCardProps) => {
  return (
    <Card
      className="shadow-soft hover:shadow-elevated transition-all cursor-pointer hover:scale-105"
      onClick={onClick}
    >
      <CardContent className="p-6 text-center">
        <div className="w-32 h-32 mx-auto mb-4 rounded-full bg-gradient-card flex items-center justify-center overflow-hidden">
          {image ? (
            <img 
              src={image} 
              alt={name}
              className="w-full h-full object-cover"
              style={{ objectPosition: imagePosition }}
            />
          ) : (
            <User className="h-16 w-16 text-white" />
          )}
        </div>
        <h3 className="text-xl font-bold text-denari-1">{name}</h3>
        <p className="text-sm text-primary font-medium mt-1">{role}</p>
      </CardContent>
    </Card>
  );
};
