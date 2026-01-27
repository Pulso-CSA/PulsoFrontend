import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { testBackendConnection, testMultipleBackendUrls, getApiConfig, ConnectionTestResult } from '@/lib/testConnection';
import { Loader2, CheckCircle2, XCircle, AlertCircle, RefreshCw } from 'lucide-react';

export function BackendConnectionTest() {
  const [isTesting, setIsTesting] = useState(false);
  const [result, setResult] = useState<ConnectionTestResult | null>(null);
  const [multipleResults, setMultipleResults] = useState<ConnectionTestResult[]>([]);
  const [showMultiple, setShowMultiple] = useState(false);
  
  const config = getApiConfig();

  const handleTest = async () => {
    setIsTesting(true);
    setResult(null);
    setMultipleResults([]);
    
    try {
      const testResult = await testBackendConnection();
      setResult(testResult);
    } catch (error: any) {
      setResult({
        success: false,
        url: config.apiBaseUrl,
        message: `Erro: ${error.message}`,
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleTestMultiple = async () => {
    setIsTesting(true);
    setResult(null);
    setMultipleResults([]);
    setShowMultiple(true);
    
    try {
      const results = await testMultipleBackendUrls();
      setMultipleResults(results);
    } catch (error: any) {
      setMultipleResults([{
        success: false,
        url: 'N/A',
        message: `Erro: ${error.message}`,
      }]);
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          Teste de Conexão com Backend
        </CardTitle>
        <CardDescription>
          Verifique se o frontend está conectado ao backend
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Configuração atual */}
        <div className="space-y-2 p-4 bg-muted rounded-lg">
          <h4 className="text-sm font-semibold">Configuração Atual:</h4>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">URL Base:</span>
              <code className="px-2 py-1 bg-background rounded text-xs">{config.apiBaseUrl}</code>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">VITE_API_URL:</span>
              <Badge variant={config.viteApiUrl === 'não definida' ? 'destructive' : 'default'}>
                {config.viteApiUrl}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Tipo:</span>
              <Badge variant={config.isRelative ? 'secondary' : 'default'}>
                {config.isRelative ? 'URL Relativa' : 'URL Absoluta'}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Ambiente:</span>
              <Badge>{config.environment}</Badge>
            </div>
          </div>
        </div>

        {/* Botões de teste */}
        <div className="flex gap-2">
          <Button 
            onClick={handleTest} 
            disabled={isTesting}
            className="flex-1"
          >
            {isTesting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testando...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Testar Conexão
              </>
            )}
          </Button>
          <Button 
            onClick={handleTestMultiple} 
            disabled={isTesting}
            variant="outline"
            className="flex-1"
          >
            Testar Múltiplas URLs
          </Button>
        </div>

        {/* Resultado único */}
        {result && !showMultiple && (
          <div className={`p-4 rounded-lg border-2 ${
            result.success 
              ? 'bg-green-50 dark:bg-green-950 border-green-500' 
              : 'bg-red-50 dark:bg-red-950 border-red-500'
          }`}>
            <div className="flex items-start gap-3">
              {result.success ? (
                <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
              )}
              <div className="flex-1 space-y-1">
                <p className={`font-semibold ${
                  result.success 
                    ? 'text-green-900 dark:text-green-100' 
                    : 'text-red-900 dark:text-red-100'
                }`}>
                  {result.success ? 'Conexão Estabelecida!' : 'Falha na Conexão'}
                </p>
                <p className="text-sm text-muted-foreground">
                  {result.message}
                </p>
                <div className="flex gap-4 text-xs text-muted-foreground mt-2">
                  <span>URL: <code className="bg-background px-1 rounded">{result.url}</code></span>
                  {result.status && (
                    <span>Status: <Badge variant="outline">{result.status}</Badge></span>
                  )}
                  {result.responseTime && (
                    <span>Tempo: {result.responseTime}ms</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Resultados múltiplos */}
        {showMultiple && multipleResults.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Resultados dos Testes:</h4>
            {multipleResults.map((testResult, index) => (
              <div 
                key={index}
                className={`p-3 rounded-lg border ${
                  testResult.success 
                    ? 'bg-green-50 dark:bg-green-950 border-green-500' 
                    : 'bg-red-50 dark:bg-red-950 border-red-500'
                }`}
              >
                <div className="flex items-start gap-2">
                  {testResult.success ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <code className="text-xs bg-background px-1.5 py-0.5 rounded break-all">
                        {testResult.url}
                      </code>
                      {testResult.status && (
                        <Badge variant="outline" className="text-xs">
                          {testResult.status}
                        </Badge>
                      )}
                      {testResult.responseTime && (
                        <span className="text-xs text-muted-foreground">
                          {testResult.responseTime}ms
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {testResult.message}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Aviso sobre configuração */}
        {config.viteApiUrl === 'não definida' && (
          <div className="p-3 bg-yellow-50 dark:bg-yellow-950 border border-yellow-500 rounded-lg">
            <p className="text-sm text-yellow-900 dark:text-yellow-100">
              <strong>Aviso:</strong> A variável de ambiente <code>VITE_API_URL</code> não está definida.
              O frontend está usando a URL relativa <code>/api</code> como padrão.
            </p>
            <p className="text-xs text-yellow-800 dark:text-yellow-200 mt-2">
              Para configurar, crie um arquivo <code>.env</code> na raiz do projeto com:
            </p>
            <pre className="mt-2 p-2 bg-background rounded text-xs overflow-x-auto">
              VITE_API_URL=http://localhost:8000/api
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
