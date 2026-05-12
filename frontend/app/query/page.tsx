"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Send,
  AlertCircle,
  Loader2,
  Copy,
  CheckCircle2,
} from "lucide-react";
import { invoiceAPI } from "@/lib/api";
import { toast } from "sonner";

const EXAMPLE_QUERIES = [
  "Show me approved invoices from ACME CORPORATION",
  "Find all invoices with PO-2847",
];

interface QueryResult {
  success: boolean;
  message: string;
  query_understanding: {
    intent: string;
    invoice_number: string | null;
    po_number: string | null;
    vendor: string | null;
    status: string | null;
    risk_level: string | null;
    semantic_query: string;
    metadata_filters: Record<string, any>;
  };
  filtered_documents_count: number;
  dense_results_count: number;
  sparse_results_count: number;
  fused_results_count: number;
  retrieved_context: string;
  final_answer: string;
}

export default function InvoiceQuery() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      toast.error("Please enter a search query");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await invoiceAPI.queryInvoices(searchQuery, 3);
      setResult(response);
      toast.success("Query executed successfully!");
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to query invoices";
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(query);
  };

  const copyToClipboard = () => {
    if (result?.final_answer) {
      navigator.clipboard.writeText(result.final_answer);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStatusBadgeColor = (status: string | null) => {
    if (!status) return "bg-slate-600";
    const lower = status.toLowerCase();
    if (lower === "approved")
      return "bg-success-500/20 text-success-300 border-success-500/30";
    if (lower === "rejected")
      return "bg-danger-500/20 text-danger-300 border-danger-500/30";
    if (lower === "pending")
      return "bg-warning-500/20 text-warning-300 border-warning-500/30";
    return "bg-slate-600";
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-700 to-primary-600">
          Invoice Query
        </h1>
        <p className="text-slate-600 mt-2">
          Ask questions about your invoices in natural language
        </p>
      </div>

      {/* Search Card */}
      <Card className="bg-slate-800 border-slate-700 shadow-lg">
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 pointer-events-none" />
                <Input
                  type="text"
                  placeholder="Ask about invoices... e.g., 'Show approved invoices from ACME CORPORATION'"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-12 bg-slate-700 border-slate-600 text-slate-100 placeholder:text-slate-500 focus:border-primary-500"
                  disabled={loading}
                />
              </div>
              <Button
                type="submit"
                disabled={loading || !query.trim()}
                className="bg-primary-600 hover:bg-primary-700 text-white px-6 gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Search
                  </>
                )}
              </Button>
            </div>

            {/* Example Queries */}
            <div className="pt-4 border-t border-slate-700">
              <p className="text-xs text-slate-400 uppercase tracking-widest font-semibold mb-3">
                Try these queries:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {EXAMPLE_QUERIES.map((example) => (
                  <button
                    key={example}
                    onClick={() => {
                      setQuery(example);
                      setTimeout(() => handleSearch(example), 100);
                    }}
                    disabled={loading}
                    className="text-left text-xs px-3 py-2 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-slate-100 transition-colors border border-slate-600 hover:border-slate-500 disabled:opacity-50"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert className="bg-danger-500/10 border-danger-500/30">
          <AlertCircle className="h-4 w-4 text-danger-400" />
          <AlertDescription className="text-danger-200">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Card className="bg-primary-500/10 border-primary-500/30">
          <CardContent className="pt-6 text-center space-y-4">
            <div className="flex justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary-400" />
            </div>
            <p className="text-slate-300">Processing your query...</p>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="space-y-6 animate-in fade-in duration-500">
          {/* Query Understanding */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="border-b border-slate-700">
              <CardTitle className="text-base text-slate-100">
                Query Understanding
              </CardTitle>
              <CardDescription className="text-slate-400">
                AI interpreted your query as:
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
                    Intent
                  </p>
                  <Badge className="bg-primary-500/20 text-primary-300 border-primary-500/30">
                    {result.query_understanding.intent}
                  </Badge>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  {result.query_understanding.vendor && (
                    <div>
                      <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
                        Vendor
                      </p>
                      <Badge className="bg-slate-700 text-slate-200">
                        {result.query_understanding.vendor}
                      </Badge>
                    </div>
                  )}

                  {result.query_understanding.po_number && (
                    <div>
                      <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
                        PO Number
                      </p>
                      <Badge className="bg-slate-700 text-slate-200">
                        {result.query_understanding.po_number}
                      </Badge>
                    </div>
                  )}

                  {result.query_understanding.status && (
                    <div>
                      <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
                        Status
                      </p>
                      <Badge
                        className={`border ${getStatusBadgeColor(result.query_understanding.status)}`}
                      >
                        {result.query_understanding.status}
                      </Badge>
                    </div>
                  )}

                  {result.query_understanding.risk_level && (
                    <div>
                      <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
                        Risk Level
                      </p>
                      <Badge className="bg-slate-700 text-slate-200">
                        {result.query_understanding.risk_level}
                      </Badge>
                    </div>
                  )}
                </div>

                <div>
                  <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
                    Semantic Query
                  </p>
                  <p className="text-sm text-slate-300 italic">
                    {result.query_understanding.semantic_query}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Search Statistics */}
          <div className="grid md:grid-cols-4 gap-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="pt-6">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Documents Found
                </p>
                <p className="text-3xl font-bold text-primary-400 mt-2">
                  {result.filtered_documents_count}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="pt-6">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Dense Results
                </p>
                <p className="text-3xl font-bold text-success-400 mt-2">
                  {result.dense_results_count}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="pt-6">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Sparse Results
                </p>
                <p className="text-3xl font-bold text-warning-400 mt-2">
                  {result.sparse_results_count}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="pt-6">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Fused Results
                </p>
                <p className="text-3xl font-bold text-primary-300 mt-2">
                  {result.fused_results_count}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Final Answer */}
          <Card className="bg-gradient-to-br from-primary-500/10 to-slate-800 border-primary-500/30 shadow-lg">
            <CardHeader className="border-b border-primary-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-success-400" />
                  <CardTitle className="text-lg text-slate-100">
                    Answer
                  </CardTitle>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={copyToClipboard}
                  className="text-slate-400 hover:text-slate-200"
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="prose prose-invert max-w-none">
                <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">
                  {result.final_answer}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Retrieved Context */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="border-b border-slate-700">
              <CardTitle className="text-base text-slate-100">
                Retrieved Context
              </CardTitle>
              <CardDescription className="text-slate-400">
                Raw documents from the search
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="bg-slate-900 rounded-lg p-4 text-sm text-slate-300 font-mono overflow-x-auto max-h-96 overflow-y-auto">
                {String(result.retrieved_context || "")
                  .split("\n")
                  .map((line, idx) => (
                    <div key={idx}>{line}</div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* No Results Yet */}
      {!result && !loading && !error && (
        <Card className="bg-slate-800/50 border-slate-700/50 border-dashed">
          <CardContent className="pt-12 text-center space-y-4 pb-12">
            <Search className="w-12 h-12 text-slate-600 mx-auto" />
            <div>
              <p className="text-slate-300 font-medium">Start searching</p>
              <p className="text-slate-500 text-sm">
                Enter a query above to search your invoices
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
