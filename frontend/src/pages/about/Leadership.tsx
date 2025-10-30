import { TeamCard } from "@/components/TeamCard";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useState } from "react";
import { Users } from "lucide-react";

const teamMembers = [
  {
    name: "Sophia Guiter",
    role: "Chief Executive Officer",
    bio: "Sophia brings over 15 years of experience in financial services and technology. Prior to founding Denari, she led product development at a major investment bank, where she saw firsthand the need for better valuation tools. Her vision is to make professional-grade financial modeling accessible to investment professionals worldwide.",
  },
  {
    name: "Ian Ortega",
    role: "Chief Operating Officer",
    bio: "Ian's operational expertise comes from scaling multiple fintech startups. He previously served as VP of Operations at a leading financial data platform. Ian ensures that Denari's infrastructure can support the demands of institutional investors while maintaining the agility of a growing company.",
  },
  {
    name: "Sam Brooks",
    role: "Chief Technology Officer",
    bio: "Sam is a software architect with a passion for building robust, scalable systems. Before joining Denari, Sam led engineering teams at both startups and Fortune 500 companies. Sam's technical vision ensures that Denari remains at the forefront of financial technology innovation.",
  },
  {
    name: "Aiden Beeskow",
    role: "Chief Financial Officer",
    bio: "Aiden is a CPA with extensive experience in both public accounting and corporate finance. Previously a senior manager at a Big Four firm, Aiden brings deep expertise in financial modeling and reporting. Aiden's background ensures that Denari's models meet the highest professional standards.",
  },
];

export default function Leadership() {
  const [selectedMember, setSelectedMember] = useState<typeof teamMembers[0] | null>(null);

  return (
    <div className="min-h-screen">
      <div className="relative h-64 bg-gradient-hero overflow-hidden">
        <div className="absolute inset-0 bg-denari-1/50 backdrop-blur-sm" />
        <div className="relative h-full flex items-center justify-center">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-4 rounded-full bg-primary/20">
                <Users className="h-12 w-12 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-white">Leadership Team</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {teamMembers.map((member) => (
              <TeamCard
                key={member.name}
                name={member.name}
                role={member.role}
                bio={member.bio}
                onClick={() => setSelectedMember(member)}
              />
            ))}
          </div>
        </div>
      </div>

      <Dialog open={!!selectedMember} onOpenChange={() => setSelectedMember(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl">{selectedMember?.name}</DialogTitle>
            <p className="text-primary font-medium">{selectedMember?.role}</p>
          </DialogHeader>
          <div className="mt-4">
            <p className="text-muted-foreground leading-relaxed">{selectedMember?.bio}</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
