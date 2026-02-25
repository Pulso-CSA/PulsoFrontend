import { Component, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      const isDev = import.meta.env.DEV;
      const err = this.state.error;

      return (
        <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center">
          <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-8 max-w-2xl w-full">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-foreground mb-2">
              Algo deu errado
            </h2>
            <p className="text-muted-foreground text-sm mb-4">
              Ocorreu um erro inesperado. Tente recarregar a página.
            </p>
            {isDev && err && (
              <div className="mb-6 p-4 rounded-lg bg-muted/50 text-left overflow-auto max-h-48">
                <p className="text-xs font-mono text-destructive break-all mb-2">
                  {err.message}
                </p>
                {err.stack && (
                  <pre className="text-[10px] text-muted-foreground whitespace-pre-wrap break-all">
                    {err.stack}
                  </pre>
                )}
              </div>
            )}
            <Button onClick={this.handleRetry} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Tentar novamente
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
