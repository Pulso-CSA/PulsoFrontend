// Função utilitária para testar conexão com o backend
// Usa a mesma URL que api.ts para garantir consistência (proxy em dev, direto em prod/Electron)
import { getApiBaseUrl } from '@/lib/api';

export interface ConnectionTestResult {
  success: boolean;
  url: string;
  status?: number;
  message: string;
  responseTime?: number;
}

/**
 * Testa a conexão com o backend fazendo uma requisição simples
 */
export async function testBackendConnection(): Promise<ConnectionTestResult> {
  const startTime = Date.now();
  const base = getApiBaseUrl().replace(/\/$/, "");
  const testUrl = `${base}/health`;
  
  try {
    const response = await fetch(testUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const responseTime = Date.now() - startTime;
    
    if (response.ok) {
      return {
        success: true,
        url: testUrl,
        status: response.status,
        message: 'Conexão com backend estabelecida com sucesso!',
        responseTime,
      };
    } else {
      return {
        success: false,
        url: testUrl,
        status: response.status,
        message: `Backend respondeu com status ${response.status}`,
        responseTime,
      };
    }
  } catch (error: any) {
    const responseTime = Date.now() - startTime;
    
    // Verificar se é erro de CORS
    if (error.message?.includes('CORS') || error.message?.includes('Failed to fetch')) {
      return {
        success: false,
        url: testUrl,
        message: `Erro de CORS ou backend não está acessível. Verifique se o backend está rodando e se a URL está correta. URL atual: ${base}`,
        responseTime,
      };
    }
    
    return {
      success: false,
      url: testUrl,
      message: `Erro ao conectar: ${error.message || 'Erro desconhecido'}. URL atual: ${base}`,
      responseTime,
    };
  }
}

/**
 * Testa múltiplas URLs possíveis do backend
 */
export async function testMultipleBackendUrls(): Promise<ConnectionTestResult[]> {
  const possibleUrls = [getApiBaseUrl(), "https://pulsoapi-production-f227.up.railway.app", "http://127.0.0.1:8000"];
  
  const results: ConnectionTestResult[] = [];
  
  for (const baseUrl of possibleUrls) {
    const startTime = Date.now();
    const testUrl = `${baseUrl}/health`;
    
    try {
      const response = await fetch(testUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const responseTime = Date.now() - startTime;
      
      results.push({
        success: response.ok,
        url: testUrl,
        status: response.status,
        message: response.ok 
          ? 'Conexão estabelecida!' 
          : `Status ${response.status}`,
        responseTime,
      });
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      results.push({
        success: false,
        url: testUrl,
        message: error.message || 'Erro desconhecido',
        responseTime,
      });
    }
  }
  
  return results;
}

/**
 * Obtém informações sobre a configuração atual da API
 */
export function getApiConfig() {
  return {
    apiBaseUrl: getApiBaseUrl(),
    viteApiUrl: (import.meta.env.VITE_API_URL || 'não definida').toString().trim(),
    isRelative: !getApiBaseUrl().startsWith('http'),
    environment: import.meta.env.MODE,
  };
}
