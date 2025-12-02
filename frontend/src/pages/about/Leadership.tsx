import { TeamCard } from "@/components/TeamCard";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useState } from "react";
import { Users } from "lucide-react";

const teamMembers = [
  {
    name: "Sophia Guiter",
    role: "Chief Executive Officer",
    bio: "Sophia Guiter is a senior at Marquette University studying Finance, Information Systems, and the AIM fintech program. She has experince working for buy-side firms, knowing the current shortcomings and opportunities for a new research platform. Sophia drives strategic thinking in the group and helps align project work with real-world financial applications.",
    image: "/leadership/sophia-guiter.JPG",
    imagePosition: "45% 60%", // Adjust this value to position the photo (horizontal% vertical%)
  },
  {
    name: "Ian Ortega",
    role: "Chief Operating Officer",
    bio: "Ian Ortega is a senior honors student at Marquette University studying Biomedical Engineering (Biocomputing) with a minor in Computer Engineering. He is passionate about applying AI and CAD/design tools to solve complex engineering challenges. Ian contributes a unique intersection of technical ingenuity, research orientation, and innovation focus to the team.",
    image: "/leadership/ian-ortega.JPG",
    imagePosition: "45% 45%", // Adjust this value to position the photo (horizontal% vertical%)
  },
  {
    name: "Sam Brooks",
    role: "Chief Technology Officer",
    bio: "Sam Brooks is a senior at Marquette University studying Information Systems and the AIM fintech program. He has experience with data engineering for startups as well as valuing companies with his involvement in the Dorm Fund. Sam brings a structured, tech-savvy mindset to the group, bridging coding with systems thinking.",
    image: "/leadership/sam-brooks.JPG",
    imagePosition: "50% 45%", // Adjust this value to position the photo (horizontal% vertical%)
  },
  {
    name: "Aiden Beeskow",
    role: "Chief Financial Officer",
    bio: "Aiden Beeskow is a senior at Marquette University studying Accounting and the AIM FinTech track. He combines strong numerical acumen with fintech interest and a disciplined approach to deliverables. Aiden anchors financial analysis, quality assurance, and ensures rigorous execution of analytical work. Previously a senior manager at a Big Four firm, Aiden brings deep expertise in financial modeling and reporting. Aiden's background ensures that Denari's models meet the highest professional standards.",
    image: "/leadership/aiden-beeskow.JPG",
    imagePosition: "50% 20%", // Adjust this value to position the photo (horizontal% vertical%)
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
                image={member.image}
                imagePosition={member.imagePosition}
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
