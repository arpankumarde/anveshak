import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  Shield,
  Zap,
  Terminal,
  Activity,
  GitBranch,
  Cpu,
  Globe,
  MessageSquare,
  Github,
  Twitter,
  Linkedin
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0f3433] text-[#e0f7f6] selection:bg-[#facc15] selection:text-[#0f3433] font-sans flex flex-col">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 backdrop-blur-md bg-[#0f3433]/80 border-b border-[#2d5c5a]">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#facc15] flex items-center justify-center">
              <Zap className="w-5 h-5 text-[#0f3433] fill-current" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">Anveshak</span>
          </div>

          <Link
            href="/dashboard"
            className="px-5 py-2 rounded-full bg-[#facc15] text-[#0f3433] font-semibold text-sm hover:bg-[#ffe066] transition-colors shadow-[0_0_15px_rgba(250,204,21,0.3)] hover:shadow-[0_0_25px_rgba(250,204,21,0.5)] flex items-center gap-2"
          >
            Dashboard
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-grow pt-32 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col items-center text-center space-y-8 mb-24">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#1a4d4b] border border-[#2d5c5a] text-[#facc15] text-xs font-medium uppercase tracking-wider">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#facc15] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#facc15]"></span>
              </span>
              Intelligent Log Orchestration
            </div>

            <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white max-w-4xl leading-tight">
              Turn Chaos into <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#facc15] to-[#fde047]">Clarity</span> with AI Agents
            </h1>

            <p className="text-lg md:text-xl text-[#94b8b6] max-w-2xl leading-relaxed">
              Anveshak proactively analyzes, interprets, and acts upon log data through a sophisticated network of specialized AI agents. Stop reacting to incidents, prevent them.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Link
                href="/dashboard"
                className="px-8 py-4 rounded-xl bg-[#facc15] text-[#0f3433] font-bold text-lg hover:bg-[#ffe066] transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(250,204,21,0.2)]"
              >
                Get Started
              </Link>
              <button className="px-8 py-4 rounded-xl bg-[#1a4d4b] text-white font-semibold text-lg hover:bg-[#235e5c] border border-[#2d5c5a] transition-all">
                View Documentation
              </button>
            </div>
          </div>

          {/* Feature Grid */}
          <div className="grid md:grid-cols-3 gap-6 mb-32">
            <FeatureCard
              title="Autonomous Agents"
              description="A supervisor-pattern multi-agent architecture that functions as your autonomous DevOps engineer."
              icon={<Zap className="w-6 h-6 text-[#facc15]" />}
            />
            <FeatureCard
              title="Proactive Detection"
              description="Detect anomalies and loopholes before they impact users with hybrid ML and rule-based reasoning."
              icon={<Shield className="w-6 h-6 text-[#facc15]" />}
            />
            <FeatureCard
              title="Contextual Insight"
              description="Preserve context across interactions to correlate metrics with errors and trace root causes."
              icon={<BarChart3 className="w-6 h-6 text-[#facc15]" />}
            />
          </div>

          {/* Intelligent Orchestration Section */}
          <div className="mb-32">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Orchestrated Intelligence</h2>
              <p className="text-[#94b8b6] max-w-2xl mx-auto text-lg">
                A supervisor-pattern architecture where specialized agents work in concert to solve complex observability challenges.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <AgentCard
                title="Parser Agent"
                icon={<Terminal className="w-6 h-6 text-[#facc15]" />}
                desc="Normalizes unstructured logs into standardized formats automatically."
              />
              <AgentCard
                title="Anomaly Detector"
                icon={<Activity className="w-6 h-6 text-[#facc15]" />}
                desc="Identifies subtle deviations using unsupervised ML models."
              />
              <AgentCard
                title="Correlation Agent"
                icon={<GitBranch className="w-6 h-6 text-[#facc15]" />}
                desc="Links error logs with infrastructure metrics and deployment events."
              />
              <AgentCard
                title="RCA Agent"
                icon={<Cpu className="w-6 h-6 text-[#facc15]" />}
                desc="Performs deep forensic analysis to identify root causes instantly."
              />
            </div>
          </div>

          {/* Integration Section */}
          <div className="py-20 border-y border-[#2d5c5a]/50 mb-20">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Seamless Integration</h2>
              <p className="text-[#94b8b6] max-w-2xl mx-auto text-lg">
                Connects effortlessly with your existing DevOps toolchain and cloud infrastructure.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-4">
              {['Docker', 'Kubernetes', 'AWS', 'PM2', 'Prometheus', 'Grafana', 'Elasticsearch', 'Slack', 'PagerDuty', 'GitHub'].map((tech) => (
                <span key={tech} className="px-6 py-3 rounded-full bg-[#1a4d4b]/40 border border-[#2d5c5a] text-[#e0f7f6] font-medium hover:border-[#facc15]/50 hover:bg-[#1a4d4b] transition-all cursor-default select-none">
                  {tech}
                </span>
              ))}
            </div>
          </div>

          {/* CTA Section */}
          <div className="mb-24 text-center rounded-3xl bg-gradient-to-br from-[#123f3d] to-[#0f3433] p-12 border border-[#2d5c5a] relative overflow-hidden group">
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Ready to Modernize Your Observability?</h2>
              <p className="text-[#94b8b6] max-w-2xl mx-auto mb-10 text-lg">
                Join forward-thinking engineering teams using Anveshak to reduce MTTR and prevent incidents before they happen.
              </p>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-[#facc15] text-[#0f3433] font-bold text-lg hover:bg-[#ffe066] transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(250,204,21,0.2)]"
              >
                Start Monitoring Now
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
            <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/2 w-80 h-80 bg-[#facc15] rounded-full blur-[120px] opacity-[0.08] group-hover:opacity-[0.12] transition-opacity"></div>
            <div className="absolute bottom-0 left-0 translate-y-1/2 -translate-x-1/2 w-64 h-64 bg-[#facc15] rounded-full blur-[100px] opacity-[0.05] group-hover:opacity-[0.1] transition-opacity"></div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#2d5c5a] bg-[#0d2e2d] pt-16 pb-8 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-7 h-7 rounded bg-[#facc15] flex items-center justify-center">
                  <Zap className="w-4 h-4 text-[#0f3433] fill-current" />
                </div>
                <span className="text-xl font-bold text-white">Anveshak</span>
              </div>
              <p className="text-[#94b8b6] max-w-xs mb-8 leading-relaxed">
                Intelligent multi-agent orchestration for modern application observability. Detect, analyze, and resolve proactively.
              </p>
              <div className="flex gap-4">
                <SocialIcon icon={<Globe className="w-5 h-5" />} />
                <SocialIcon icon={<Github className="w-5 h-5" />} />
                <SocialIcon icon={<Twitter className="w-5 h-5" />} />
                <SocialIcon icon={<Linkedin className="w-5 h-5" />} />
              </div>
            </div>

            <div>
              <h4 className="font-bold text-white mb-6">Product</h4>
              <ul className="space-y-4 text-[#94b8b6]">
                <li><Link href="#" className="hover:text-[#facc15] transition-colors">Features</Link></li>
                <li><Link href="#" className="hover:text-[#facc15] transition-colors">Integrations</Link></li>
                <li><Link href="#" className="hover:text-[#facc15] transition-colors">Security</Link></li>
                <li><Link href="#" className="hover:text-[#facc15] transition-colors">Enterprise</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-bold text-white mb-6">Resources</h4>
              <ul className="space-y-4 text-[#94b8b6]">
                <li><Link href="#" className="hover:text-[#facc15] transition-colors">Documentation</Link></li>
                <li><Link href="#" className="hover:text-[#facc15] transition-colors">API Reference</Link></li>
                <li><Link href="#" className="hover:text-[#facc15] transition-colors">Community</Link></li>
                <li><Link href="#" className="hover:text-[#facc15] transition-colors">Blog</Link></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-[#2d5c5a] flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-[#5c8583]">
            <p>&copy; {new Date().getFullYear()} Anveshak. All rights reserved.</p>
            <div className="flex gap-8">
              <Link href="#" className="hover:text-[#e0f7f6] transition-colors">Privacy Policy</Link>
              <Link href="#" className="hover:text-[#e0f7f6] transition-colors">Terms of Service</Link>
              <Link href="#" className="hover:text-[#e0f7f6] transition-colors">Cookie Policy</Link>
            </div>
          </div>
        </div>
      </footer>

      {/* Background Elements */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#1a4d4b] rounded-full blur-[120px] opacity-30"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-[#facc15] rounded-full blur-[150px] opacity-10"></div>
      </div>
    </div>
  );
}

function FeatureCard({ title, description, icon }: { title: string, description: string, icon: React.ReactNode }) {
  return (
    <div className="group p-8 rounded-2xl bg-[#0f3433] border border-[#2d5c5a] hover:border-[#facc15]/50 transition-all hover:bg-[#133e3c]">
      <div className="w-12 h-12 rounded-lg bg-[#1a4d4b] flex items-center justify-center mb-6 border border-[#2d5c5a] group-hover:border-[#facc15]/30 transition-colors">
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-[#facc15] transition-colors">{title}</h3>
      <p className="text-[#94b8b6] leading-relaxed">
        {description}
      </p>
    </div>
  );
}

function AgentCard({ title, desc, icon }: { title: string, desc: string, icon: React.ReactNode }) {
  return (
    <div className="p-6 rounded-2xl bg-[#123f3d]/50 border border-[#2d5c5a] hover:bg-[#1a4d4b] hover:border-[#facc15]/30 transition-all group">
      <div className="mb-4 p-3 bg-[#0f3433] rounded-xl inline-block border border-[#2d5c5a] group-hover:border-[#facc15]/20 group-hover:scale-110 transition-all duration-300">
        {icon}
      </div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-[#94b8b6] text-sm leading-relaxed">
        {desc}
      </p>
    </div>
  );
}

function SocialIcon({ icon }: { icon: React.ReactNode }) {
  return (
    <Link
      href="#"
      className="w-10 h-10 rounded-full bg-[#1a4d4b] flex items-center justify-center text-[#94b8b6] hover:bg-[#facc15] hover:text-[#0f3433] transition-all transform hover:scale-110"
    >
      {icon}
    </Link>
  );
}

