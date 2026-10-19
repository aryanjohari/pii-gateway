import { Footer } from "@/components/Footer";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { Playground } from "@/components/Playground";
import { SelfHost } from "@/components/SelfHost";
import { SiteNav } from "@/components/SiteNav";

export default function HomePage() {
  return (
    <div className="mx-auto min-h-screen w-full max-w-5xl px-5 pb-16 pt-6 sm:px-8">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-5 focus:top-2 focus:z-10 focus:rounded-full focus:bg-ink focus:px-4 focus:py-2 focus:text-sm focus:text-paper"
      >
        Skip to main content
      </a>
      <SiteNav />
      <main id="main" className="mt-10 space-y-24 sm:mt-14 sm:space-y-28">
        <Hero />
        <Playground />
        <HowItWorks />
        <SelfHost />
      </main>
      <Footer />
    </div>
  );
}
