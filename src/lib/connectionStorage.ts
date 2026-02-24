/**
 * Persistência de dados de conexão e credenciais em localStorage.
 * ⚠️ Atenção: credenciais ficam no navegador. Evite em computadores compartilhados.
 */

// Chaves de storage
const DB_CONNECTION_KEY = 'pulso_db_connection';
const DATA_CHAT_CONTEXT_KEY = 'pulso_data_chat_context';
const CLOUD_CONFIG_PREFIX = 'cloudConfig_'; // compatível com CloudChat existente
const ROOT_PATH_KEY = 'pulso_root_path';
const FINOPS_CREDENTIALS_KEY = 'pulso_finops_credentials';
const DATA_CHAT_SESSIONS_KEY = 'pulso_data_chat_sessions';
const FINOPS_CHAT_SESSIONS_KEY = 'pulso_finops_chat_sessions';
const CLOUD_CHAT_SESSIONS_KEY = 'pulso_cloud_chat_sessions';

/** Contexto da conversa Inteligência de Dados (id_requisicao, dataset_ref, model_ref) */
export type DataChatContext = {
  idRequisicao: string;
  datasetRef?: string | null;
  modelRef?: string | null;
};

export function getDataChatContext(): DataChatContext | null {
  try {
    const raw = sessionStorage.getItem(DATA_CHAT_CONTEXT_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as DataChatContext;
    return data && typeof data === 'object' && typeof data.idRequisicao === 'string' ? data : null;
  } catch {
    return null;
  }
}

export function setDataChatContext(ctx: DataChatContext): void {
  sessionStorage.setItem(DATA_CHAT_CONTEXT_KEY, JSON.stringify(ctx));
}

export function clearDataChatContext(): void {
  sessionStorage.removeItem(DATA_CHAT_CONTEXT_KEY);
}

// Tipos
export type DbConnectionData = {
  type: string;
  host: string;
  database: string;
  user: string;
  password: string;
};

export type AwsCredentials = {
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
  accountId: string;
};

export type AzureCredentials = {
  region: string;
  tenantId: string;
  clientId: string;
  clientSecret: string;
  subscriptionId: string;
};

export type GcpCredentials = {
  region: string;
  projectId: string;
  clientEmail: string;
  privateKey: string;
};

export type CloudCredentials = {
  aws: AwsCredentials;
  azure: AzureCredentials;
  gcp: GcpCredentials;
};

// Conexão de banco (DataChat)
export function getDbConnection(): DbConnectionData | null {
  try {
    const raw = localStorage.getItem(DB_CONNECTION_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as DbConnectionData;
    return data && typeof data === 'object' ? data : null;
  } catch {
    return null;
  }
}

export function setDbConnection(data: DbConnectionData): void {
  localStorage.setItem(DB_CONNECTION_KEY, JSON.stringify(data));
}

export function clearDbConnection(): void {
  localStorage.removeItem(DB_CONNECTION_KEY);
}

// Credenciais Cloud (CloudChat)
export function getCloudCredentials(provider: 'aws' | 'azure' | 'gcp'): AwsCredentials | AzureCredentials | GcpCredentials | null {
  try {
    const raw = localStorage.getItem(`${CLOUD_CONFIG_PREFIX}${provider}`);
    if (!raw) return null;
    return JSON.parse(raw) as AwsCredentials | AzureCredentials | GcpCredentials;
  } catch {
    return null;
  }
}

export function setCloudCredentials(provider: 'aws' | 'azure' | 'gcp', data: AwsCredentials | AzureCredentials | GcpCredentials): void {
  localStorage.setItem(`${CLOUD_CONFIG_PREFIX}${provider}`, JSON.stringify(data));
}

export function getAllCloudCredentials(): CloudCredentials {
  const defaults = {
    aws: { region: '', accessKeyId: '', secretAccessKey: '', accountId: '' },
    azure: { region: '', tenantId: '', clientId: '', clientSecret: '', subscriptionId: '' },
    gcp: { region: '', projectId: '', clientEmail: '', privateKey: '' },
  };
  const aws = getCloudCredentials('aws') ?? defaults.aws;
  const azure = getCloudCredentials('azure') ?? defaults.azure;
  const gcp = getCloudCredentials('gcp') ?? defaults.gcp;
  return { aws, azure, gcp };
}

// Root path (CloudChat)
export function getRootPath(): string {
  return localStorage.getItem(ROOT_PATH_KEY) ?? '';
}

export function setRootPath(path: string): void {
  if (path.trim()) {
    localStorage.setItem(ROOT_PATH_KEY, path);
  } else {
    localStorage.removeItem(ROOT_PATH_KEY);
  }
}

/** Sessões de chat (histórico de conversas completas) */
export type ChatSession<T = unknown> = {
  id: string;
  title: string;
  messages: T[];
  createdAt: string;
  updatedAt: string;
  context?: Record<string, unknown>;
};

export function getDataChatSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(DATA_CHAT_SESSIONS_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw) as ChatSession[];
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export function setDataChatSessions(sessions: ChatSession[]): void {
  localStorage.setItem(DATA_CHAT_SESSIONS_KEY, JSON.stringify(sessions));
}

export function getFinOpsChatSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(FINOPS_CHAT_SESSIONS_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw) as ChatSession[];
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export function setFinOpsChatSessions(sessions: ChatSession[]): void {
  localStorage.setItem(FINOPS_CHAT_SESSIONS_KEY, JSON.stringify(sessions));
}

export function getCloudChatSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(CLOUD_CHAT_SESSIONS_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw) as ChatSession[];
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export function setCloudChatSessions(sessions: ChatSession[]): void {
  localStorage.setItem(CLOUD_CHAT_SESSIONS_KEY, JSON.stringify(sessions));
}
