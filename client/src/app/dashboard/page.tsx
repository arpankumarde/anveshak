"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertCircle,
  TrendingUp,
  Activity,
  Zap,
  Lightbulb,
  Layers,
  Plus,
  FlaskConical,
  AlertTriangle,
  Settings,
  FileText,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";

const Page = () => {
  const [isInsightsOpen, setIsInsightsOpen] = useState(false);
  const [isCrashesOpen, setIsCrashesOpen] = useState(false);
  const [selectedInsight, setSelectedInsight] = useState<
    (typeof insights)[0] | null
  >(null);
  const [selectedCrash, setSelectedCrash] = useState<
    (typeof crashes)[0] | null
  >(null);
  const [isCrashConfirmOpen, setIsCrashConfirmOpen] = useState(false);

  // Configuration form state with prefilled values
  const [config, setConfig] = useState({
    whatsappNumber: "+919876543201",
    email: "admin@anveshak.com",
    githubRepo: "mernbaba/test-repo",
    githubToken: "ghp_xxxxxxxxxxxx",
    websocketUrl: "ws://65.0.0.233:8000",
  });

  const handleSaveConfig = () => {
    // Save configuration logic would go here
    toast.success("Configuration saved successfully");
  };

  // Recent logs state
  interface LogEntry {
    _id: string;
    data: string;
    category: string;
    cluster_type: string;
    severity: number;
    timestamp: number;
    created_at: string;
    connection_id: string;
    is_anomaly: boolean;
  }

  const [recentLogs, setRecentLogs] = useState<LogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);

  // Fetch recent logs function
  const fetchRecentLogs = async () => {
    setLogsLoading(true);
    try {
      const response = await fetch(
        "https://wbnl3r1d-8000.inc1.devtunnels.ms/api/logs/recent"
      );
      if (!response.ok) {
        throw new Error("Failed to fetch logs");
      }
      const data = await response.json();
      setRecentLogs(data.logs || []);
      toast.success("Logs refreshed successfully");
    } catch (error) {
      console.error("Error fetching recent logs:", error);
      toast.error("Failed to load recent logs");
    } finally {
      setLogsLoading(false);
    }
  };

  // Fetch recent logs on mount
  useEffect(() => {
    fetchRecentLogs();
  }, []);

  // Stats state
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsData, setStatsData] = useState({
    total_logs: 0,
    processed_logs: 0,
    errors: 0,
    crashes: 0,
    insights: 0,
    clusters: 0,
  });

  // Fetch stats from API
  useEffect(() => {
    const fetchStats = async () => {
      setStatsLoading(true);
      try {
        const response = await fetch(
          "https://wbnl3r1d-8000.inc1.devtunnels.ms/api/counts"
        );
        if (!response.ok) {
          throw new Error("Failed to fetch stats");
        }
        const data = await response.json();
        setStatsData({
          total_logs: data.total_logs || 0,
          processed_logs: data.processed_logs || 0,
          errors: data.errors || 0,
          crashes: data.crashes || 0,
          insights: data.insights || 0,
          clusters: data.clusters || 0,
        });
      } catch (error) {
        console.error("Error fetching stats:", error);
        toast.error("Failed to load statistics");
      } finally {
        setStatsLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Format number with commas
  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  // Stat cards data
  const stats = [
    {
      title: "Total Logs",
      value: formatNumber(statsData.total_logs),
      change: "+12%",
      icon: Activity,
      gradient: "from-blue-400 to-cyan-400",
      bgColor: "bg-blue-50",
    },
    {
      title: "Processed Logs",
      value: formatNumber(statsData.processed_logs),
      change: "+8%",
      icon: Zap,
      gradient: "from-purple-400 to-pink-400",
      bgColor: "bg-purple-50",
    },
    {
      title: "Errors",
      value: formatNumber(statsData.errors),
      change: "-5%",
      icon: AlertCircle,
      gradient: "from-red-400 to-orange-400",
      bgColor: "bg-red-50",
    },
    {
      title: "Crashes",
      value: formatNumber(statsData.crashes),
      change: "0%",
      icon: AlertCircle,
      gradient: "from-rose-400 to-red-400",
      bgColor: "bg-rose-50",
    },
    {
      title: "Insights",
      value: formatNumber(statsData.insights),
      change: "+15%",
      icon: Lightbulb,
      gradient: "from-yellow-400 to-amber-400",
      bgColor: "bg-yellow-50",
    },
    {
      title: "Clusters",
      value: formatNumber(statsData.clusters),
      change: "+22%",
      icon: Layers,
      gradient: "from-green-400 to-emerald-400",
      bgColor: "bg-green-50",
    },
  ];

  const insights = [
    {
      id: "1",
      insight_type: "periodic",
      insight: "Detected 5 errors in last 10 minutes across API service",
      impact_level: "MEDIUM",
      recommendation: "Review high severity errors immediately",
      trend_analysis: "Active monitoring: 25 clusters created",
      error_count: 5,
      high_severity_count: 2,
      created_at: "2025-01-15T10:30:00Z",
      severity: 6,
    },
    {
      id: "2",
      insight_type: "batch",
      insight: "Unusual spike in database connection timeouts detected",
      impact_level: "HIGH",
      recommendation: "Check database connection pool and increase if needed",
      trend_analysis: "Pattern detected: 3 similar incidents in past hour",
      error_count: 12,
      high_severity_count: 8,
      created_at: "2025-01-15T09:15:00Z",
      severity: 8,
    },
    {
      id: "3",
      insight_type: "periodic",
      insight: "Memory usage trending upward in production environment",
      impact_level: "LOW",
      recommendation: "Monitor memory patterns and consider optimization",
      trend_analysis: "Gradual increase over 2 hours",
      error_count: 0,
      high_severity_count: 0,
      created_at: "2025-01-15T08:45:00Z",
      severity: 3,
    },
    {
      id: "4",
      insight_type: "batch",
      insight: "Critical crash detected in payment processing service",
      impact_level: "HIGH",
      recommendation: "Immediate investigation required - service may be down",
      trend_analysis: "First occurrence in 24 hours",
      error_count: 1,
      high_severity_count: 1,
      created_at: "2025-01-15T07:20:00Z",
      severity: 9,
    },
    {
      id: "5",
      insight_type: "periodic",
      insight: "Increased latency in user authentication endpoint",
      impact_level: "MEDIUM",
      recommendation: "Review authentication service performance",
      trend_analysis: "Consistent pattern over last 30 minutes",
      error_count: 3,
      high_severity_count: 1,
      created_at: "2025-01-15T06:10:00Z",
      severity: 5,
    },
    {
      id: "6",
      insight_type: "periodic",
      insight: "CPU usage spike detected in worker processes",
      impact_level: "LOW",
      recommendation: "Monitor CPU usage patterns and consider scaling",
      trend_analysis: "Temporary spike lasting 15 minutes",
      error_count: 0,
      high_severity_count: 0,
      created_at: "2025-01-15T05:30:00Z",
      severity: 2,
    },
    {
      id: "7",
      insight_type: "batch",
      insight: "Unusual pattern in API response times",
      impact_level: "MEDIUM",
      recommendation: "Investigate API performance bottlenecks",
      trend_analysis: "Response times increased by 200ms on average",
      error_count: 0,
      high_severity_count: 0,
      created_at: "2025-01-15T04:15:00Z",
      severity: 3,
    },
    {
      id: "8",
      insight_type: "periodic",
      insight: "Database query optimization opportunity identified",
      impact_level: "LOW",
      recommendation: "Review slow query logs and optimize indexes",
      trend_analysis: "5 queries taking longer than 1 second",
      error_count: 0,
      high_severity_count: 0,
      created_at: "2025-01-15T03:45:00Z",
      severity: 1,
    },
    {
      id: "9",
      insight_type: "batch",
      insight: "Network latency increase in external API calls",
      impact_level: "MEDIUM",
      recommendation: "Check external service status and network connectivity",
      trend_analysis: "Latency increased by 150ms over last hour",
      error_count: 0,
      high_severity_count: 0,
      created_at: "2025-01-15T02:20:00Z",
      severity: 3,
    },
  ];

  const crashes = [
    {
      id: "1",
      crash_type: "application_crash",
      severity: 9,
      crash_indicators: ["segmentation fault", "null pointer exception"],
      affected_components: ["api-service", "database"],
      recovery_status: "automatic",
      immediate_actions: [
        "Restart service",
        "Check logs",
        "Verify database connection",
      ],
      root_cause: "Memory leak causing out of memory (OOM) error",
      prevention:
        "Fix memory leak in service, implement proper resource cleanup",
      resolved: false,
      created_at: "2025-01-15T10:45:00Z",
      timestamp: "2025-01-15T10:44:30Z",
    },
    {
      id: "2",
      crash_type: "database_connection_failure",
      severity: 8,
      crash_indicators: ["connection timeout", "connection pool exhausted"],
      affected_components: ["database", "payment-service"],
      recovery_status: "manual",
      immediate_actions: [
        "Increase connection pool size",
        "Check database server status",
      ],
      root_cause: "Database connection pool exhausted due to high traffic",
      prevention: "Implement connection pooling limits and monitoring",
      resolved: false,
      created_at: "2025-01-15T09:20:00Z",
      timestamp: "2025-01-15T09:19:15Z",
    },
    {
      id: "3",
      crash_type: "service_unavailable",
      severity: 7,
      crash_indicators: ["503 service unavailable", "health check failed"],
      affected_components: ["auth-service"],
      recovery_status: "automatic",
      immediate_actions: ["Restart service", "Check health endpoints"],
      root_cause: "Service health check failed due to dependency timeout",
      prevention: "Improve dependency timeout handling and circuit breakers",
      resolved: true,
      created_at: "2025-01-15T08:10:00Z",
      timestamp: "2025-01-15T08:09:45Z",
    },
    {
      id: "4",
      crash_type: "application_crash",
      severity: 9,
      crash_indicators: ["stack overflow", "infinite recursion"],
      affected_components: ["analytics-service"],
      recovery_status: "manual",
      immediate_actions: [
        "Review code for recursion",
        "Add stack depth limits",
      ],
      root_cause: "Infinite recursion in analytics processing function",
      prevention:
        "Add recursion depth limits and proper termination conditions",
      resolved: false,
      created_at: "2025-01-15T07:30:00Z",
      timestamp: "2025-01-15T07:29:20Z",
    },
    {
      id: "5",
      crash_type: "system_crash",
      severity: 10,
      crash_indicators: ["kernel panic", "system reboot"],
      affected_components: ["infrastructure", "all-services"],
      recovery_status: "automatic",
      immediate_actions: ["Check system logs", "Verify infrastructure health"],
      root_cause: "System resource exhaustion leading to kernel panic",
      prevention: "Implement resource monitoring and auto-scaling",
      resolved: false,
      created_at: "2025-01-15T06:00:00Z",
      timestamp: "2025-01-15T05:59:10Z",
    },
  ];

  const getSeverityColor = (severity: number) => {
    if (severity >= 8) return "bg-red-600 text-white";
    if (severity >= 4) return "bg-amber-500 text-white";
    return "bg-blue-500 text-white";
  };

  const getSeverityLabel = (severity: number) => {
    if (severity >= 8) return "SEVERE";
    if (severity >= 4) return "MEDIUM";
    return "LOW";
  };

  const isErrorInsight = (insight: (typeof insights)[0]) => {
    return insight.error_count > 0;
  };

  const handleCreateIssue = async (insight: (typeof insights)[0]) => {
    try {
      const response = await fetch("http://localhost:8000/create-issue", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: insight.insight,
          description: `${insight.recommendation}\n\nTrend Analysis: ${insight.trend_analysis}`,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create issue");
      }

      const data = await response.json();
      const { issue_url, issue_number } = data;

      // Show success message with issue number
      toast.success(
        `Issue #${issue_number} created successfully. Redirecting...`
      );

      // Redirect to issue URL in new tab after 3 seconds
      setTimeout(() => {
        if (issue_url) {
          window.open(issue_url, "_blank");
        }
      }, 3000);
    } catch (error) {
      toast.error("Failed to create issue");
      console.error("Error creating issue:", error);
    }
  };

  const handleSimulateCrash = async () => {
    try {
      toast.loading("Simulating crash...");

      // Send email
      const emailResponse = await fetch("http://localhost:8000/send-email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          subject: "Sending with Twilio SendGrid is Fun",
          html_content:
            "<strong>and easy to do anywhere, even with Python</strong>",
        }),
      });

      if (!emailResponse.ok) {
        console.warn("Failed to send email, continuing...");
      }

      // Send WhatsApp message
      const whatsappResponse = await fetch(
        "http://localhost:8000/send-whatsapp-message",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message:
              "🚨 *Critical Alert*\n\nSimulated crash detected in Anveshak system.\n\nThis is a test crash generated from the dashboard experiment section.\n\nSeverity: 9 (SEVERE)\nTime: " +
              new Date().toLocaleString(),
          }),
        }
      );

      if (!whatsappResponse.ok) {
        console.warn("Failed to send WhatsApp message, continuing...");
      }

      toast.dismiss();
      toast.success(
        "Crash simulated successfully. Email and WhatsApp notifications sent."
      );
    } catch (error) {
      toast.dismiss();
      toast.error(
        error instanceof Error ? error.message : "Failed to simulate crash"
      );
      console.error("Error simulating crash:", error);
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "HIGH":
        return "bg-red-100 text-red-700 border-red-200";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-700 border-yellow-200";
      case "LOW":
        return "bg-green-100 text-green-700 border-green-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-slate-600/30 p-4">
      <div className="max-w-7xl mx-auto space-y-4">
        {/* Header */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-1">
            <Image
              src="/logo.png"
              alt="Anveshak Logo"
              width={32}
              height={32}
              className="rounded-lg"
            />
            <h1 className="text-3xl font-bold text-slate-900">Anveshak</h1>
          </div>
          <p className="text-sm text-slate-600 ml-10">
            Intelligent Multi-Agent Log Orchestration Dashboard
          </p>
        </div>

        {/* Stats Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {statsLoading
            ? stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <Card
                    key={index}
                    className="bg-muted border border-slate-200 shadow-sm py-4 gap-2"
                  >
                    <CardHeader className="flex flex-row items-center justify-between px-4">
                      <Skeleton className="h-6 w-24 bg-slate-400" />
                      <div
                        className={`p-1.5 rounded-lg bg-gradient-to-br ${stat.gradient} text-white shadow-sm`}
                      >
                        <Icon className="size-8" />
                      </div>
                    </CardHeader>
                    <CardContent className="px-4">
                      <Skeleton className="h-8 w-20 mb-2 bg-slate-400" />
                      <Skeleton className="h-4 w-32 bg-slate-400" />
                    </CardContent>
                  </Card>
                );
              })
            : stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <Card
                    key={index}
                    className="bg-muted border border-slate-200 shadow-sm hover:shadow-md transition-all duration-300 hover:border-indigo-300 py-4 gap-2"
                  >
                    <CardHeader className="flex flex-row items-center justify-between px-4">
                      <CardTitle className="text-xl font-medium text-slate-700">
                        {stat.title}
                      </CardTitle>
                      <div
                        className={`p-1.5 rounded-lg bg-gradient-to-br ${stat.gradient} text-white shadow-sm`}
                      >
                        <Icon className="size-8" />
                      </div>
                    </CardHeader>
                    <CardContent className="px-4">
                      <div className="text-2xl font-bold text-slate-900 mb-1">
                        {stat.value}
                      </div>
                      <div className="flex items-center gap-1.5 text-xs">
                        <TrendingUp className="h-3 w-3 text-emerald-600" />
                        <span className="text-slate-600">
                          {stat.change} from last period
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
        </div>

        {/* Experiment Section - Split into 1/3 and 2/3 */}
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Simulate Crash Section - 1/3 */}
          <Card className="bg-muted border border-slate-200 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2 mb-1">
                <FlaskConical className="h-4 w-4 text-indigo-600" />
                <CardTitle className="text-lg font-semibold text-slate-900">
                  Experiment
                </CardTitle>
              </div>
              <CardDescription className="text-sm text-slate-600">
                Simulate system events for testing
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0 space-y-4">
              <Button
                onClick={() => setIsCrashConfirmOpen(true)}
                className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white shadow-lg font-semibold"
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                Simulate a Crash
              </Button>

              {/* Simulated Crash Details Preview */}
              <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <Badge className="bg-red-600 text-white border-0 text-xs">
                    SEVERE (Severity: 9)
                  </Badge>
                  <Badge
                    variant="outline"
                    className="bg-red-100 text-red-700 border-red-200 text-xs"
                  >
                    Unresolved
                  </Badge>
                  <Badge variant="outline" className="border-slate-300 text-xs">
                    Simulated Crash
                  </Badge>
                </div>
                <div className="space-y-2 text-sm">
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1 text-xs">
                      Root Cause
                    </h4>
                    <p className="text-slate-700 text-xs">
                      Simulated crash from dashboard experiment
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1 text-xs">
                      Prevention
                    </h4>
                    <p className="text-slate-700 text-xs">
                      This is a test crash
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1 text-xs">
                      Crash Indicators
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      <Badge
                        variant="outline"
                        className="border-red-300 text-red-700 text-xs"
                      >
                        Simulated crash for testing
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1 text-xs">
                      Affected Components
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      <Badge
                        variant="outline"
                        className="border-slate-300 text-xs"
                      >
                        dashboard
                      </Badge>
                      <Badge
                        variant="outline"
                        className="border-slate-300 text-xs"
                      >
                        experiment
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1 text-xs">
                      Immediate Actions
                    </h4>
                    <ul className="list-disc list-inside text-slate-700 space-y-0.5 text-xs">
                      <li>Review crash logs</li>
                      <li>Check system status</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Configuration Section - 2/3 */}
          <Card className="bg-muted border border-slate-200 shadow-sm lg:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2 mb-1">
                <Settings className="h-4 w-4 text-indigo-600" />
                <CardTitle className="text-lg font-semibold text-slate-900">
                  Configuration
                </CardTitle>
              </div>
              <CardDescription className="text-sm text-slate-600">
                Configure notification and repository settings
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="space-y-2">
                  <Label htmlFor="whatsapp">WhatsApp Number</Label>
                  <Input
                    id="whatsapp"
                    type="tel"
                    placeholder="+1234567890"
                    value={config.whatsappNumber}
                    onChange={(e) =>
                      setConfig({ ...config, whatsappNumber: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="your.email@example.com"
                    value={config.email}
                    onChange={(e) =>
                      setConfig({ ...config, email: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="githubRepo">GitHub Repository</Label>
                  <Input
                    id="githubRepo"
                    type="text"
                    placeholder="mernbaba/test-repo"
                    value={config.githubRepo}
                    onChange={(e) =>
                      setConfig({ ...config, githubRepo: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="githubToken">GitHub Token</Label>
                  <Input
                    id="githubToken"
                    type="password"
                    placeholder="ghp_xxxxxxxxxxxx"
                    value={config.githubToken}
                    onChange={(e) =>
                      setConfig({ ...config, githubToken: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="websocketUrl">WebSocket URL</Label>
                  <Input
                    id="websocketUrl"
                    type="text"
                    placeholder="ws://localhost:8000"
                    value={config.websocketUrl}
                    onChange={(e) =>
                      setConfig({ ...config, websocketUrl: e.target.value })
                    }
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <Button
                  onClick={handleSaveConfig}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  Save Configuration
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Insights and Crashes Section - Side by Side */}
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Insights Section */}
          <Card className="bg-muted border border-slate-200 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl font-bold text-slate-900 mb-1">
                    Recent Insights
                  </CardTitle>
                  <CardDescription className="text-sm text-slate-600">
                    Click on an insight to view details
                  </CardDescription>
                </div>
                <Button
                  onClick={() => setIsInsightsOpen(true)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
                >
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="max-h-[500px] overflow-y-auto pr-2 space-y-3">
                {insights.map((insight) => (
                  <div
                    key={insight.id}
                    className="p-3 rounded-lg border border-slate-200 hover:border-indigo-300 bg-white transition-all duration-200 hover:shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div
                        className="flex-1 cursor-pointer"
                        onClick={() => setSelectedInsight(insight)}
                      >
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                          <Badge
                            className={`${getSeverityColor(
                              insight.severity
                            )} border-0 text-xs`}
                          >
                            {getSeverityLabel(insight.severity)}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={`${getImpactColor(
                              insight.impact_level
                            )} border text-xs`}
                          >
                            {insight.impact_level} Impact
                          </Badge>
                        </div>
                        <p className="text-slate-900 font-medium mb-1 text-sm">
                          {insight.insight}
                        </p>
                        <p className="text-xs text-slate-600 line-clamp-2">
                          {insight.recommendation}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <div className="text-right">
                          <div className="text-xs text-slate-500 mb-1">
                            {formatDate(insight.created_at)}
                          </div>
                          {insight.error_count > 0 && (
                            <div className="text-xs text-slate-600">
                              {insight.error_count} errors
                            </div>
                          )}
                        </div>
                        {!isErrorInsight(insight) && (
                          <Button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCreateIssue(insight);
                            }}
                            variant="outline"
                            size="sm"
                            className="border-indigo-300 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-400 text-xs h-7 px-2"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            Create Issue
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Crashes Section */}
          <Card className="bg-muted border border-slate-200 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl font-bold text-slate-900 mb-1">
                    Recent Crashes
                  </CardTitle>
                  <CardDescription className="text-sm text-slate-600">
                    Click on a crash to view details
                  </CardDescription>
                </div>
                <Button
                  onClick={() => setIsCrashesOpen(true)}
                  className="bg-red-600 hover:bg-red-700 text-white shadow-sm"
                >
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3">
                {crashes.slice(0, 3).map((crash) => (
                  <div
                    key={crash.id}
                    onClick={() => setSelectedCrash(crash)}
                    className="p-3 rounded-lg border border-slate-200 hover:border-red-300 bg-white cursor-pointer transition-all duration-200 hover:shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                          <Badge
                            className={`${getSeverityColor(
                              crash.severity
                            )} border-0 text-xs`}
                          >
                            {getSeverityLabel(crash.severity)}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={`${
                              crash.resolved
                                ? "bg-green-100 text-green-700 border-green-200"
                                : "bg-red-100 text-red-700 border-red-200"
                            } border text-xs`}
                          >
                            {crash.resolved ? "Resolved" : "Unresolved"}
                          </Badge>
                          <Badge
                            variant="outline"
                            className="border-slate-300 text-xs"
                          >
                            {crash.crash_type
                              .replace(/_/g, " ")
                              .replace(/\b\w/g, (l) => l.toUpperCase())}
                          </Badge>
                        </div>
                        <p className="text-slate-900 font-medium mb-1 text-sm">
                          {crash.crash_type
                            .replace(/_/g, " ")
                            .replace(/\b\w/g, (l) => l.toUpperCase())}
                        </p>
                        <p className="text-xs text-slate-600 line-clamp-2">
                          {crash.root_cause}
                        </p>
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          {crash.affected_components
                            .slice(0, 3)
                            .map((component, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className="text-xs border-slate-300"
                              >
                                {component}
                              </Badge>
                            ))}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-slate-500 mb-1">
                          {formatDate(crash.created_at)}
                        </div>
                        <div className="text-xs text-slate-600">
                          Severity: {crash.severity}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Logs Section */}
        <div className="mt-4">
          <Card className="border border-slate-700/50 shadow-sm bg-muted gap-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="h-4 w-4 text-indigo-400" />
                    <CardTitle className="text-lg font-semibold">
                      Recent Logs
                    </CardTitle>
                  </div>
                  <CardDescription className="text-sm">
                    Latest system logs and events
                  </CardDescription>
                </div>
                <Button
                  onClick={fetchRecentLogs}
                  size="sm"
                  className="bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 shadow-sm"
                  disabled={logsLoading}
                >
                  <RefreshCw
                    className={`h-4 w-4 mr-2 ${
                      logsLoading ? "animate-spin" : ""
                    }`}
                  />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {logsLoading ? (
                <div
                  className="min-h-dvh flex items-center justify-center text-slate-400 font-mono"
                  style={{ backgroundColor: "#1e1e1e" }}
                >
                  Loading logs...
                </div>
              ) : recentLogs.length === 0 ? (
                <div
                  className="min-h-[80dvh] flex items-center justify-center text-slate-400 font-mono"
                  style={{ backgroundColor: "#1e1e1e" }}
                >
                  No logs available
                </div>
              ) : (
                <div
                  className="min-h-[80dvh] max-h-[80dvh] overflow-y-auto pr-2 space-y-2 p-4 rounded-lg"
                  style={{ backgroundColor: "#1e1e1e" }}
                >
                  {recentLogs.map((log) => {
                    // Parse the data field which is a string representation of a tuple
                    let logMessage = "";
                    try {
                      // Try to parse as JSON first
                      const jsonMatch = log.data.match(/\{.*\}/);
                      if (jsonMatch) {
                        const parsed = JSON.parse(jsonMatch[0]);
                        logMessage =
                          parsed.message || parsed.timestamp || log.data;
                      } else {
                        // Try to extract message from tuple-like string
                        const messageMatch = log.data.match(
                          /message['"]?\s*:\s*['"]([^'"]+)['"]/
                        );
                        if (messageMatch) {
                          logMessage = messageMatch[1];
                        } else {
                          logMessage = log.data;
                        }
                      }
                    } catch {
                      logMessage = log.data;
                    }

                    const formatTimestamp = (timestamp: number) => {
                      const date = new Date(timestamp * 1000);
                      return date.toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      });
                    };

                    // Check if severe or critical (severity >= 8)
                    const isSevere = (log.severity || 0) >= 8;
                    const isCritical = (log.severity || 0) >= 9;

                    // Get color based on severity/category
                    const getLogColor = () => {
                      if (isCritical) return "text-red-300";
                      if (isSevere) return "text-orange-300";
                      if (log.severity >= 4) return "text-yellow-300";
                      if (log.category === "ERROR") return "text-red-300";
                      if (log.category === "WARNING") return "text-yellow-300";
                      return "text-emerald-300";
                    };

                    // Get border color - red for severe/critical
                    const getBorderColor = () => {
                      if (isCritical) return "border-red-500";
                      if (isSevere) return "border-orange-500";
                      return "border-emerald-400/60";
                    };

                    // Get background for severe/critical
                    const getBackground = () => {
                      if (isCritical) return "hover:bg-red-900/20";
                      if (isSevere) return "hover:bg-orange-900/15";
                      return "hover:bg-slate-800/30";
                    };

                    return (
                      <div
                        key={log._id}
                        className={`font-mono text-sm border-l-2 ${getBorderColor()} pl-3 py-1.5 ${getBackground()} transition-colors rounded-r ${
                          isSevere ? "ring-1 ring-red-500/20" : ""
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <span className="text-slate-500 text-xs shrink-0">
                            {log.timestamp
                              ? formatTimestamp(log.timestamp)
                              : log.created_at || "N/A"}
                          </span>
                          <span
                            className={`${getLogColor()} shrink-0 text-xs font-semibold`}
                          >
                            [{log.category || "UNKNOWN"}]
                          </span>
                          <span
                            className={`${
                              isSevere ? "text-red-300" : "text-slate-300"
                            } flex-1 break-words`}
                          >
                            {logMessage}
                          </span>
                          {log.severity !== undefined && (
                            <span
                              className={`${
                                isSevere ? "text-red-400" : "text-slate-500"
                              } text-xs shrink-0 font-semibold`}
                            >
                              [sev:{log.severity}]
                            </span>
                          )}
                        </div>
                        {log.connection_id && (
                          <div className="text-slate-600 text-xs mt-1 ml-20">
                            → connection: {log.connection_id}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Insights Dialog */}
      <Dialog open={isInsightsOpen} onOpenChange={setIsInsightsOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-slate-900">
              All Insights
            </DialogTitle>
            <DialogDescription>
              Complete list of system insights with severity and impact analysis
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {insights.map((insight) => (
              <Card
                key={insight.id}
                className="border border-slate-200 hover:border-indigo-300 transition-all duration-200"
              >
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        className={`${getSeverityColor(
                          insight.severity
                        )} border-0`}
                      >
                        {getSeverityLabel(insight.severity)} (Severity:{" "}
                        {insight.severity})
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`${getImpactColor(
                          insight.impact_level
                        )} border`}
                      >
                        {insight.impact_level} Impact
                      </Badge>
                      <Badge variant="outline" className="border-slate-300">
                        {insight.insight_type}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-500">
                      {formatDate(insight.created_at)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Insight
                    </h4>
                    <p className="text-slate-700">{insight.insight}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Recommendation
                    </h4>
                    <p className="text-slate-700">{insight.recommendation}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Trend Analysis
                    </h4>
                    <p className="text-slate-700">{insight.trend_analysis}</p>
                  </div>
                  {(insight.error_count > 0 ||
                    insight.high_severity_count > 0) && (
                    <div className="flex gap-4 pt-2 border-t border-slate-200">
                      {insight.error_count > 0 && (
                        <div>
                          <span className="text-sm font-medium text-slate-600">
                            Errors:{" "}
                          </span>
                          <span className="text-sm text-slate-900 font-semibold">
                            {insight.error_count}
                          </span>
                        </div>
                      )}
                      {insight.high_severity_count > 0 && (
                        <div>
                          <span className="text-sm font-medium text-slate-600">
                            High Severity:{" "}
                          </span>
                          <span className="text-sm text-red-600 font-semibold">
                            {insight.high_severity_count}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                  {!isErrorInsight(insight) && (
                    <div className="pt-2 border-t border-slate-200">
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCreateIssue(insight);
                        }}
                        variant="outline"
                        size="sm"
                        className="border-indigo-300 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-400"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Create an Issue
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Crashes Dialog */}
      <Dialog open={isCrashesOpen} onOpenChange={setIsCrashesOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-slate-900">
              All Crashes
            </DialogTitle>
            <DialogDescription>
              Complete list of system crashes with severity and recovery
              information
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {crashes.map((crash) => (
              <Card
                key={crash.id}
                className="border border-slate-200 hover:border-red-300 transition-all duration-200"
              >
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        className={`${getSeverityColor(
                          crash.severity
                        )} border-0`}
                      >
                        {getSeverityLabel(crash.severity)} (Severity:{" "}
                        {crash.severity})
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`${
                          crash.resolved
                            ? "bg-green-100 text-green-700 border-green-200"
                            : "bg-red-100 text-red-700 border-red-200"
                        } border`}
                      >
                        {crash.resolved ? "Resolved" : "Unresolved"}
                      </Badge>
                      <Badge variant="outline" className="border-slate-300">
                        {crash.crash_type
                          .replace(/_/g, " ")
                          .replace(/\b\w/g, (l) => l.toUpperCase())}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`${
                          crash.recovery_status === "automatic"
                            ? "bg-blue-100 text-blue-700 border-blue-200"
                            : "bg-amber-100 text-amber-700 border-amber-200"
                        } border`}
                      >
                        {crash.recovery_status === "automatic"
                          ? "Auto Recovery"
                          : "Manual Recovery"}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-500">
                      {formatDate(crash.created_at)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Root Cause
                    </h4>
                    <p className="text-slate-700">{crash.root_cause}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Prevention
                    </h4>
                    <p className="text-slate-700">{crash.prevention}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Crash Indicators
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {crash.crash_indicators.map((indicator, idx) => (
                        <Badge
                          key={idx}
                          variant="outline"
                          className="border-red-300 text-red-700"
                        >
                          {indicator}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Affected Components
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {crash.affected_components.map((component, idx) => (
                        <Badge
                          key={idx}
                          variant="outline"
                          className="border-slate-300"
                        >
                          {component}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Immediate Actions
                    </h4>
                    <ul className="list-disc list-inside text-slate-700 space-y-1">
                      {crash.immediate_actions.map((action, idx) => (
                        <li key={idx}>{action}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="pt-2 border-t border-slate-200">
                    <div className="text-sm text-slate-600">
                      <span className="font-medium">Timestamp: </span>
                      {formatDate(crash.timestamp)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Individual Insight Dialog */}
      <Dialog
        open={selectedInsight !== null}
        onOpenChange={(open) => !open && setSelectedInsight(null)}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedInsight && (
            <>
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-slate-900">
                  Insight Details
                </DialogTitle>
                <DialogDescription>
                  Detailed information about this insight
                </DialogDescription>
              </DialogHeader>
              <Card className="border border-slate-200">
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        className={`${getSeverityColor(
                          selectedInsight.severity
                        )} border-0`}
                      >
                        {getSeverityLabel(selectedInsight.severity)} (Severity:{" "}
                        {selectedInsight.severity})
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`${getImpactColor(
                          selectedInsight.impact_level
                        )} border`}
                      >
                        {selectedInsight.impact_level} Impact
                      </Badge>
                      <Badge variant="outline" className="border-slate-300">
                        {selectedInsight.insight_type}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-500">
                      {formatDate(selectedInsight.created_at)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Insight
                    </h4>
                    <p className="text-slate-700">{selectedInsight.insight}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Recommendation
                    </h4>
                    <p className="text-slate-700">
                      {selectedInsight.recommendation}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Trend Analysis
                    </h4>
                    <p className="text-slate-700">
                      {selectedInsight.trend_analysis}
                    </p>
                  </div>
                  {(selectedInsight.error_count > 0 ||
                    selectedInsight.high_severity_count > 0) && (
                    <div className="flex gap-4 pt-2 border-t border-slate-200">
                      {selectedInsight.error_count > 0 && (
                        <div>
                          <span className="text-sm font-medium text-slate-600">
                            Errors:{" "}
                          </span>
                          <span className="text-sm text-slate-900 font-semibold">
                            {selectedInsight.error_count}
                          </span>
                        </div>
                      )}
                      {selectedInsight.high_severity_count > 0 && (
                        <div>
                          <span className="text-sm font-medium text-slate-600">
                            High Severity:{" "}
                          </span>
                          <span className="text-sm text-red-600 font-semibold">
                            {selectedInsight.high_severity_count}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                  {!isErrorInsight(selectedInsight) && (
                    <div className="pt-2 border-t border-slate-200">
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCreateIssue(selectedInsight);
                        }}
                        variant="outline"
                        size="sm"
                        className="border-indigo-300 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-400"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Create an Issue
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Individual Crash Dialog */}
      <Dialog
        open={selectedCrash !== null}
        onOpenChange={(open) => !open && setSelectedCrash(null)}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedCrash && (
            <>
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-slate-900">
                  Crash Details
                </DialogTitle>
                <DialogDescription>
                  Detailed information about this crash
                </DialogDescription>
              </DialogHeader>
              <Card className="border border-slate-200">
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        className={`${getSeverityColor(
                          selectedCrash.severity
                        )} border-0`}
                      >
                        {getSeverityLabel(selectedCrash.severity)} (Severity:{" "}
                        {selectedCrash.severity})
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`${
                          selectedCrash.resolved
                            ? "bg-green-100 text-green-700 border-green-200"
                            : "bg-red-100 text-red-700 border-red-200"
                        } border`}
                      >
                        {selectedCrash.resolved ? "Resolved" : "Unresolved"}
                      </Badge>
                      <Badge variant="outline" className="border-slate-300">
                        {selectedCrash.crash_type
                          .replace(/_/g, " ")
                          .replace(/\b\w/g, (l) => l.toUpperCase())}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`${
                          selectedCrash.recovery_status === "automatic"
                            ? "bg-blue-100 text-blue-700 border-blue-200"
                            : "bg-amber-100 text-amber-700 border-amber-200"
                        } border`}
                      >
                        {selectedCrash.recovery_status === "automatic"
                          ? "Auto Recovery"
                          : "Manual Recovery"}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-500">
                      {formatDate(selectedCrash.created_at)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Root Cause
                    </h4>
                    <p className="text-slate-700">{selectedCrash.root_cause}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Prevention
                    </h4>
                    <p className="text-slate-700">{selectedCrash.prevention}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Crash Indicators
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedCrash.crash_indicators.map((indicator, idx) => (
                        <Badge
                          key={idx}
                          variant="outline"
                          className="border-red-300 text-red-700"
                        >
                          {indicator}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Affected Components
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedCrash.affected_components.map(
                        (component, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="border-slate-300"
                          >
                            {component}
                          </Badge>
                        )
                      )}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Immediate Actions
                    </h4>
                    <ul className="list-disc list-inside text-slate-700 space-y-1">
                      {selectedCrash.immediate_actions.map((action, idx) => (
                        <li key={idx}>{action}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="pt-2 border-t border-slate-200">
                    <div className="text-sm text-slate-600">
                      <span className="font-medium">Timestamp: </span>
                      {formatDate(selectedCrash.timestamp)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Crash Simulation Confirmation Dialog */}
      <AlertDialog
        open={isCrashConfirmOpen}
        onOpenChange={setIsCrashConfirmOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              Confirm Crash Simulation
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to simulate a crash? This action is for
              testing purposes only.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>No</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setIsCrashConfirmOpen(false);
                handleSimulateCrash();
              }}
              className="bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white"
            >
              Yes
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Page;
