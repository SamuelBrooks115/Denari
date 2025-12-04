import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

// Marketing Pages
import Landing from "./pages/Landing";
import Valuation from "./pages/Valuation";
import IndustryOverview from "./pages/IndustryOverview";
import ThreeStatement from "./pages/ThreeStatement";
import RelativeValuation from "./pages/RelativeValuation";
import DCF from "./pages/DCF";
import Solutions from "./pages/Solutions";

// About Pages
import AboutIndex from "./pages/about/Index";
import Mission from "./pages/about/Mission";
import Strategy from "./pages/about/Strategy";
import Focus from "./pages/about/Focus";
import Leadership from "./pages/about/Leadership";
import News from "./pages/about/News";
import NewsDetail from "./pages/about/NewsDetail";
import Contact from "./pages/about/Contact";

// Auth Pages
import SignIn from "./pages/auth/SignIn";
import Password from "./pages/auth/Password";
import RecoverUsername from "./pages/auth/RecoverUsername";
import VerifyEmail from "./pages/auth/VerifyEmail";
import VerifyPhone from "./pages/auth/VerifyPhone";

// App Pages
import Projects from "./pages/app/Projects";
import NewProjectWizard from "./pages/app/NewProjectWizard";
import ModelPage from "./pages/app/ModelPage";
import PreferencesIndex from "./pages/app/preferences/Index";

import NotFound from "./pages/NotFound";
import IndustryScreener from "./pages/IndustryScreener";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<><Navbar /><Landing /><Footer /></>} />
          <Route path="/valuation" element={<><Navbar /><Valuation /><Footer /></>} />
          <Route path="/industry" element={<><Navbar /><IndustryOverview /><Footer /></>} />
          <Route path="/industry-screener" element={<><Navbar /><IndustryScreener /><Footer /></>} />
          <Route path="/three-statement" element={<><Navbar /><ThreeStatement /><Footer /></>} />
          <Route path="/relative-valuation" element={<><Navbar /><RelativeValuation /><Footer /></>} />
          <Route path="/dcf" element={<><Navbar /><DCF /><Footer /></>} />
          <Route path="/solutions" element={<><Navbar /><Solutions /><Footer /></>} />
          
          <Route path="/about" element={<><Navbar /><AboutIndex /><Footer /></>}>
            <Route path="mission" element={<Mission />} />
            <Route path="strategy" element={<Strategy />} />
            <Route path="focus" element={<Focus />} />
            <Route path="leadership" element={<Leadership />} />
            <Route path="news" element={<News />} />
            <Route path="news/:slug" element={<NewsDetail />} />
            <Route path="contact" element={<Contact />} />
          </Route>
          
          <Route path="/login" element={<SignIn />} />
          <Route path="/auth/password" element={<Password />} />
          <Route path="/auth/recover-username" element={<RecoverUsername />} />
          <Route path="/auth/verify-email" element={<VerifyEmail />} />
          <Route path="/auth/verify-phone" element={<VerifyPhone />} />
          
          <Route path="/app/projects" element={<><Navbar /><Projects /><Footer /></>} />
          <Route path="/app/projects/new" element={<><Navbar /><NewProjectWizard /><Footer /></>} />
          <Route path="/app/model" element={<><Navbar /><ModelPage /><Footer /></>} />
          <Route path="/app/preferences" element={<><Navbar /><PreferencesIndex /><Footer /></>} />
          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
