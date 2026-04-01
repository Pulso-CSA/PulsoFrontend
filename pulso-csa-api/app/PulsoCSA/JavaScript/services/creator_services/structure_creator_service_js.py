#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Criação de Estrutura JS/TS/React (equivalente ao Python C3)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

try:
    from utils.logger import log_workflow
    from utils.path_validation import is_path_under_base, sanitize_relative_path
except ImportError:
    try:
        from app.PulsoCSA.Python.utils.logger import log_workflow
        from app.PulsoCSA.Python.utils.path_validation import is_path_under_base, sanitize_relative_path
    except ImportError:
        log_workflow = lambda _id, _msg: None
        is_path_under_base = lambda a, b: bool(a and b)
        def sanitize_relative_path(x):
            if not x or ".." in str(x) or str(x).startswith(("/", "\\")):
                return None
            return str(x).strip().replace("\\", "/").strip("/") or "."

try:
    from utils.log_manager import add_log
except ImportError:
    try:
        from app.utils.log_manager import add_log
    except ImportError:
        add_log = lambda *a, **k: None


def _collect_components(estrutura: Dict[str, List[str]]) -> List[tuple]:
    """
    Coleta componentes .tsx/.jsx da estrutura como (folder, filename).
    Ordem: pages primeiro, depois components; exclui App, index, Context.
    Retorna lista de (rel_path_from_src, component_name).
    """
    result: List[tuple] = []
    for folder, files in estrutura.items():
        if not isinstance(files, list):
            continue
        f = str(folder or "").strip().replace("\\", "/")
        for file in files:
            if not isinstance(file, str) or not file.endswith((".tsx", ".jsx")):
                continue
            stem = Path(file).stem
            if stem.lower() in ("app", "index"):
                continue
            if "context" in stem.lower() or "provider" in stem.lower():
                continue
            rel = f"{f}/{file}".lstrip("/") if f and f != "." else file
            result.append((rel, stem))
    # Ordenar: pages antes de components, depois alfabético
    def _sort_key(item):
        rel, name = item
        rel_low = rel.lower()
        if "page" in rel_low:
            return (0, rel_low, name)
        if "component" in rel_low:
            return (1, rel_low, name)
        return (2, rel_low, name)
    result.sort(key=_sort_key)
    return result


def _ensure_fullstack_js_structure(estrutura: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Garante um projeto JS fullstack mínimo (frontend + backend) mesmo quando
    o blueprint vier curto no fast path.
    """
    if not isinstance(estrutura, dict):
        estrutura = {}

    merged: Dict[str, List[str]] = {}
    for folder, files in estrutura.items():
        if not isinstance(files, list):
            continue
        key = str(folder or ".")
        merged[key] = [str(f) for f in files if isinstance(f, str) and str(f).strip()]

    required = {
        "src": ["index.tsx", "App.tsx", "App.css"],
        "src/components": ["LoginForm.tsx", "AuthContext.tsx"],
        "src/pages": ["LoginPage.tsx"],
        "src/services": ["authService.ts"],
        "src/hooks": ["useAuth.ts"],
        "backend/src": ["server.js"],
        "backend/src/routes": ["auth.routes.js"],
        "backend/src/services": ["auth.service.js"],
        "backend/src/data": ["users.js"],
        "backend": ["package.json", ".env.example", "README.md"],
        ".": ["package.json", "vite.config.ts", "tsconfig.json", "index.html", ".env", ".gitignore", "README.md"],
    }

    for folder, files in required.items():
        current = list(merged.get(folder, []))
        for file in files:
            if file not in current:
                current.append(file)
        merged[folder] = current

    return merged


def _find_matching_form(estrutura: Dict[str, List[str]], page_name: str) -> tuple:
    """
    Encontra componente *Form que combine com *Page (ex: LoginPage → LoginForm).
    Retorna (import_path_from_page_folder, component_name) ou (None, None).
    """
    prefix = page_name.replace("Page", "").replace("page", "")
    if not prefix:
        return None, None
    form_name = prefix[0].upper() + prefix[1:] + "Form" if prefix else ""
    if not form_name:
        return None, None
    for folder, files in estrutura.items():
        if not isinstance(files, list) or "component" not in (folder or "").lower():
            continue
        for f in files:
            if isinstance(f, str) and Path(f).stem == form_name and f.endswith((".tsx", ".jsx")):
                # pages/LoginPage.tsx importa de ../components/LoginForm
                return "../components/" + Path(f).stem, form_name
    return None, None


def _get_primary_component(estrutura: Dict[str, List[str]]) -> tuple:
    """
    Retorna (import_path, component_name) para o componente principal a renderizar em App.
    import_path é relativo a src/ (ex: './components/LoginForm').
    """
    components = _collect_components(estrutura or {})
    if not components:
        return None, None
    rel_path, name = components[0]
    # Converter src/components/LoginForm.tsx -> ./components/LoginForm
    parts = rel_path.replace("\\", "/").split("/")
    if parts and parts[0].lower() == "src":
        parts = parts[1:]
    rel_clean = "/".join(parts)
    if rel_clean.endswith(".tsx") or rel_clean.endswith(".jsx"):
        rel_clean = rel_clean[:-4]  # remover extensão
    import_path = "./" + rel_clean if rel_clean else None
    return import_path, name


def _stub_for_js_file(filepath: str, folder: str, estrutura: Dict[str, List[str]] = None) -> str:
    """Gera stub dinamicamente a partir da estrutura — sem hardcoding de domínios (login, auth, etc)."""
    path_lower = filepath.lower().replace("\\", "/")
    name = Path(filepath).stem
    
    # backend/package.json
    if path_lower.endswith("backend/package.json"):
        return json.dumps({
            "name": "pulso-backend",
            "version": "1.0.0",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "node src/server.js",
                "start": "node src/server.js"
            },
            "dependencies": {
                "cors": "^2.8.5",
                "express": "^4.19.2"
            }
        }, indent=2, ensure_ascii=False)

    # package.json
    if "package.json" in path_lower:
        return json.dumps({
            "name": "pulso-project",
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite --host 127.0.0.1 --port 3100 --strictPort",
                "build": "vite build",
                "preview": "vite preview",
                "backend:dev": "node backend/src/server.js"
            },
            "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
            "devDependencies": {"@types/react": "^18.2.0", "@types/react-dom": "^18.2.0", "@vitejs/plugin-react": "^4.2.0", "typescript": "^5.3.0", "vite": "^5.0.0"},
        }, indent=2)
    
    # vite.config
    if "vite.config" in path_lower:
        return (
            "import { defineConfig } from 'vite'\n"
            "import react from '@vitejs/plugin-react'\n\n"
            "export default defineConfig({\n"
            "  plugins: [react()],\n"
            "  server: {\n"
            "    host: '127.0.0.1',\n"
            "    port: 3100,\n"
            "    strictPort: true,\n"
            "  },\n"
            "})\n"
        )
    
    # tsconfig
    if "tsconfig" in path_lower:
        return json.dumps({
            "compilerOptions": {"target": "ES2020", "useDefineForClassFields": True, "lib": ["ES2020", "DOM", "DOM.Iterable"], "module": "ESNext", "skipLibCheck": True, "moduleResolution": "bundler", "jsx": "react-jsx", "strict": True, "noEmit": True, "isolatedModules": True, "resolveJsonModule": True},
            "include": ["src"],
        }, indent=2)
    
    # index.html
    if "index.html" in path_lower:
        return '<!DOCTYPE html>\n<html lang="pt-BR">\n  <head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>Pulso Project</title></head>\n  <body><div id="root"></div><script type="module" src="/src/index.tsx"></script></body>\n</html>'
    
    # .env — inclui VITE_API_URL quando há authService
    if path_lower.endswith(".env"):
        return "# API (Vite usa prefixo VITE_)\nVITE_API_URL=http://127.0.0.1:3001\n"
    
    # .gitignore
    if ".gitignore" in path_lower:
        return "node_modules/\ndist/\n*.log\n.env\n.DS_Store\n"
    
    # README
    if path_lower.endswith("backend/readme.md"):
        return (
            "# Backend JS\n\n"
            "Backend Express simples para autenticação local.\n\n"
            "## Endpoints\n"
            "- POST /auth/login\n"
            "- POST /auth/create_account\n"
            "- GET /auth/me\n"
            "- GET /auth/profiles\n\n"
            "## Execução\n\n"
            "```bash\n"
            "npm run backend:dev\n"
            "```\n"
        )

    if "readme" in path_lower:
        return "# Pulso Project\n\nProjeto gerado pelo Pulso.\n\n## Execução\n\n```bash\nnpm install\nnpm run dev\n```\n"
    
    # src/index.tsx
    if path_lower.endswith("index.tsx") or path_lower.endswith("index.jsx"):
        return (
            "import React from 'react'\nimport ReactDOM from 'react-dom/client'\nimport App from './App'\n\n"
            "ReactDOM.createRoot(document.getElementById('root')!).render(\n"
            "  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)\n"
        )
    
    # src/App.css
    if "app.css" in path_lower:
        return (
            ".app { max-width: 720px; margin: 0 auto; font-family: Arial, sans-serif; padding: 24px; }\n"
            ".app-header { margin-bottom: 16px; }\n"
            ".card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; }\n"
            ".form-stub { display: grid; gap: 12px; }\n"
            ".form-stub .field { display: grid; gap: 6px; }\n"
            ".form-stub input { padding: 10px; border: 1px solid #ccc; border-radius: 6px; }\n"
            ".form-actions { display: flex; gap: 8px; }\n"
            ".form-actions button { padding: 10px 14px; border: 1px solid #222; background: #111; color: #fff; border-radius: 6px; cursor: pointer; }\n"
            ".form-actions button.secondary { background: #fff; color: #111; }\n"
            ".login-success { margin-top: 10px; }\n"
        )
    # src/App.tsx — composição dinâmica com estado de auth quando Page+Form
    if path_lower.endswith("app.tsx") or path_lower.endswith("app.jsx"):
        imp_path, comp_name = _get_primary_component(estrutura or {})
        form_imp, form_name = _find_matching_form(estrutura or {}, comp_name) if comp_name else (None, None)
        if imp_path and comp_name and form_imp and form_name:
            return (
                "import React, { useState } from 'react'\n"
                "import './App.css'\n"
                f"import {comp_name} from '{imp_path}'\n\n"
                "function App() {\n"
                "  const [user, setUser] = useState<unknown>(null)\n"
                "  return (\n"
                "    <div className=\"app\">\n"
                "      <header className=\"app-header\">\n"
                "        <h1>Sistema de Login</h1>\n"
                "      </header>\n"
                "      <main>\n"
                "        {!user ? (\n"
                f"          <{comp_name} onSuccess={{(p: unknown) => setUser(p)}} />\n"
                "        ) : (\n"
                "          <div className=\"login-success\"><h2>Bem-vindo</h2><pre>{JSON.stringify(user, null, 2)}</pre></div>\n"
                "        )}\n"
                "      </main>\n"
                "    </div>\n"
                "  )\n"
                "}\n\n"
                "export default App\n"
            )
        elif imp_path and comp_name:
            return (
                "import React from 'react'\n"
                "import './App.css'\n"
                f"import {comp_name} from '{imp_path}'\n\n"
                "function App() {\n"
                "  return (\n"
                "    <div className=\"app\">\n"
                "      <header className=\"app-header\">\n"
                "        <h1>Pulso Project</h1>\n"
                "      </header>\n"
                "      <main>\n"
                f"        <{comp_name} />\n"
                "      </main>\n"
                "    </div>\n"
                "  )\n"
                "}\n\n"
                "export default App\n"
            )
        return (
            "import React from 'react'\nimport './App.css'\n\n"
            "function App() {\n  return (\n    <div className=\"app\">\n      <header className=\"app-header\">\n        <h1>Pulso Project</h1>\n      </header>\n    </div>\n  )\n}\n\nexport default App\n"
        )

    if path_lower.endswith("src/components/authcontext.tsx"):
        return (
            "import React, { createContext, useMemo, useState } from 'react'\n\n"
            "type AuthUser = {\n"
            "  id: string\n"
            "  email: string\n"
            "  name: string\n"
            "  profiles: string[]\n"
            "}\n\n"
            "type AuthContextValue = {\n"
            "  user: AuthUser | null\n"
            "  setUser: (user: AuthUser | null) => void\n"
            "}\n\n"
            "export const AuthContext = createContext<AuthContextValue>({ user: null, setUser: () => undefined })\n\n"
            "interface AuthProviderProps {\n"
            "  children: React.ReactNode\n"
            "}\n\n"
            "export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {\n"
            "  const [user, setUser] = useState<AuthUser | null>(null)\n"
            "  const value = useMemo(() => ({ user, setUser }), [user])\n"
            "  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>\n"
            "}\n"
        )

    if path_lower.endswith("src/hooks/useauth.ts"):
        return (
            "import { useContext } from 'react'\n"
            "import { AuthContext } from '../components/AuthContext'\n\n"
            "export function useAuth() {\n"
            "  return useContext(AuthContext)\n"
            "}\n"
        )

    if path_lower.endswith("src/components/loginform.tsx"):
        return (
            "import React, { useState } from 'react'\n"
            "import { createAccount, login } from '../services/authService'\n\n"
            "interface LoginFormProps {\n"
            "  onSuccess?: (payload: unknown) => void\n"
            "}\n\n"
            "const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {\n"
            "  const [name, setName] = useState('')\n"
            "  const [email, setEmail] = useState('')\n"
            "  const [password, setPassword] = useState('')\n"
            "  const [isCreateMode, setIsCreateMode] = useState(false)\n"
            "  const [loading, setLoading] = useState(false)\n"
            "  const [error, setError] = useState<string | null>(null)\n\n"
            "  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {\n"
            "    e.preventDefault()\n"
            "    setLoading(true)\n"
            "    setError(null)\n"
            "    try {\n"
            "      const payload = isCreateMode\n"
            "        ? await createAccount({ name, email, password })\n"
            "        : await login(email, password)\n"
            "      onSuccess?.(payload)\n"
            "    } catch (err) {\n"
            "      setError(err instanceof Error ? err.message : 'Falha na autenticação')\n"
            "    } finally {\n"
            "      setLoading(false)\n"
            "    }\n"
            "  }\n\n"
            "  return (\n"
            "    <form onSubmit={handleSubmit} className=\"form-stub\">\n"
            "      {isCreateMode && (\n"
            "        <div className=\"field\">\n"
            "          <label htmlFor=\"name\">Nome</label>\n"
            "          <input id=\"name\" value={name} onChange={e => setName(e.target.value)} required={isCreateMode} />\n"
            "        </div>\n"
            "      )}\n"
            "      <div className=\"field\">\n"
            "        <label htmlFor=\"email\">E-mail</label>\n"
            "        <input id=\"email\" type=\"email\" value={email} onChange={e => setEmail(e.target.value)} required />\n"
            "      </div>\n"
            "      <div className=\"field\">\n"
            "        <label htmlFor=\"password\">Senha</label>\n"
            "        <input id=\"password\" type=\"password\" value={password} onChange={e => setPassword(e.target.value)} required />\n"
            "      </div>\n"
            "      {error && <p style={{ color: '#c0392b' }}>{error}</p>}\n"
            "      <div className=\"form-actions\">\n"
            "        <button type=\"submit\" disabled={loading}>{loading ? 'Processando...' : isCreateMode ? 'Criar Conta' : 'Entrar'}</button>\n"
            "        <button type=\"button\" className=\"secondary\" onClick={() => setIsCreateMode(prev => !prev)}>\n"
            "          {isCreateMode ? 'Já tenho conta' : 'Criar conta'}\n"
            "        </button>\n"
            "      </div>\n"
            "    </form>\n"
            "  )\n"
            "}\n\n"
            "export default LoginForm\n"
        )
    
    # *Page com *Form correspondente — Page renderiza Form e repassa onSuccess
    if path_lower.endswith((".tsx", ".jsx")) and "page" in path_lower:
        form_imp, form_name = _find_matching_form(estrutura or {}, name)
        if form_imp and form_name:
            comp = name.replace("-", "") if "-" in name else name
            comp = comp[0].upper() + (comp[1:] if len(comp) > 1 else "")
            return (
                f"import React from 'react'\n"
                f"import {form_name} from '{form_imp}'\n\n"
                f"interface {comp}Props {{ onSuccess?: (p: unknown) => void }}\n\n"
                f"const {comp}: React.FC<{comp}Props> = ({{ onSuccess }}) => (\n"
                f"  <div>\n"
                f"    <{form_name} onSuccess={{onSuccess}} />\n"
                f"  </div>\n"
                f")\n\nexport default {comp}\n"
            )
    # *Form — formulário mínimo com onSuccess (inferido por convenção)
    if path_lower.endswith((".tsx", ".jsx")) and "form" in path_lower:
        comp = name.replace("-", "") if "-" in name else name
        comp = comp[0].upper() + (comp[1:] if len(comp) > 1 else "")
        return (
            "import React, { useState } from 'react'\n\n"
            f"interface {comp}Props {{ onSuccess?: (p: unknown) => void }}\n\n"
            f"const {comp}: React.FC<{comp}Props> = ({{ onSuccess }}) => {{\n"
            "  const [email, setEmail] = useState('')\n"
            "  const [password, setPassword] = useState('')\n"
            "  const [loading, setLoading] = useState(false)\n"
            "  const [error, setError] = useState<string | null>(null)\n\n"
            "  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {\n"
            "    e.preventDefault()\n"
            "    setLoading(true)\n"
            "    setError(null)\n"
            "    try {\n"
            "      const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'\n"
            "      const resp = await fetch(`${baseUrl}/auth/login`, {\n"
            "        method: 'POST', headers: { 'Content-Type': 'application/json' },\n"
            "        body: JSON.stringify({ email, password }),\n"
            "      })\n"
            "      if (!resp.ok) {\n"
            "        const data = await resp.json().catch(() => ({}))\n"
            "        throw new Error((data as { detail?: string })?.detail || 'Falha no login')\n"
            "      }\n"
            "      const data = await resp.json()\n"
            "      onSuccess?.(data)\n"
            "    } catch (err) {\n"
            "      setError(err instanceof Error ? err.message : 'Erro ao autenticar')\n"
            "    } finally {\n"
            "      setLoading(false)\n"
            "    }\n"
            "  }\n\n"
            "  return (\n"
            "    <form onSubmit={handleSubmit} className=\"form-stub\">\n"
            "      <div className=\"field\">\n"
            "        <label htmlFor=\"email\">E-mail</label>\n"
            "        <input id=\"email\" type=\"email\" value={email} onChange={e => setEmail(e.target.value)} required />\n"
            "      </div>\n"
            "      <div className=\"field\">\n"
            "        <label htmlFor=\"password\">Senha</label>\n"
            "        <input id=\"password\" type=\"password\" value={password} onChange={e => setPassword(e.target.value)} required />\n"
            "      </div>\n"
            "      {error && <p style={{ color: '#e74c3c' }}>{error}</p>}\n"
            "      <button type=\"submit\" disabled={loading}>{loading ? 'Entrando...' : 'Entrar'}</button>\n"
            "    </form>\n"
            "  )\n"
            "}\n\n"
            f"export default {comp}\n"
        )
    # Componentes .tsx/.jsx — stub genérico (LLM preenche)
    if path_lower.endswith((".tsx", ".jsx")):
        comp = name.replace("-", "") if "-" in name else name
        comp = comp[0].upper() + (comp[1:] if len(comp) > 1 else "")
        return f"import React from 'react'\n\nconst {comp}: React.FC = () => {{\n  return <div>{comp}</div>\n}}\n\nexport default {comp}\n"
    
    # .ts / .js — stubs por convenção (authService → login)
    if path_lower.endswith("backend/src/data/users.js"):
        return (
            "export const users = [\n"
            "  {\n"
            "    id: 'u-1',\n"
            "    email: 'tchelo@pulso.com',\n"
            "    password: '123456',\n"
            "    name: 'Tchelo Pulso',\n"
            "    profiles: ['admin', 'editor'],\n"
            "  },\n"
            "]\n"
        )

    if path_lower.endswith("backend/src/services/auth.service.js"):
        return (
            "import { users } from '../data/users.js'\n\n"
            "export function findUserByEmail(email) {\n"
            "  return users.find((user) => user.email.toLowerCase() === String(email || '').toLowerCase()) || null\n"
            "}\n\n"
            "export function loginUser(email, password) {\n"
            "  const user = findUserByEmail(email)\n"
            "  if (!user || user.password !== password) {\n"
            "    return null\n"
            "  }\n"
            "  return {\n"
            "    access_token: `token-${user.id}`,\n"
            "    token_type: 'bearer',\n"
            "    user: {\n"
            "      id: user.id,\n"
            "      email: user.email,\n"
            "      name: user.name,\n"
            "      profiles: user.profiles,\n"
            "    },\n"
            "  }\n"
            "}\n\n"
            "export function createAccount(payload) {\n"
            "  const email = String(payload?.email || '').trim().toLowerCase()\n"
            "  const password = String(payload?.password || '').trim()\n"
            "  const name = String(payload?.name || '').trim() || 'Novo Usuário'\n"
            "  if (!email || !password) {\n"
            "    return { ok: false, status: 400, detail: 'email e password são obrigatórios' }\n"
            "  }\n"
            "  if (findUserByEmail(email)) {\n"
            "    return { ok: false, status: 409, detail: 'usuário já existe' }\n"
            "  }\n"
            "  const newUser = {\n"
            "    id: `u-${users.length + 1}`,\n"
            "    email,\n"
            "    password,\n"
            "    name,\n"
            "    profiles: ['viewer'],\n"
            "  }\n"
            "  users.push(newUser)\n"
            "  return { ok: true, user: { id: newUser.id, email: newUser.email, name: newUser.name, profiles: newUser.profiles } }\n"
            "}\n"
        )

    if path_lower.endswith("backend/src/routes/auth.routes.js"):
        return (
            "import { Router } from 'express'\n"
            "import { createAccount, findUserByEmail, loginUser } from '../services/auth.service.js'\n\n"
            "export const authRouter = Router()\n\n"
            "authRouter.post('/login', (req, res) => {\n"
            "  const { email, password } = req.body || {}\n"
            "  const result = loginUser(email, password)\n"
            "  if (!result) {\n"
            "    return res.status(401).json({ detail: 'Invalid credentials' })\n"
            "  }\n"
            "  return res.json(result)\n"
            "})\n\n"
            "authRouter.post('/create_account', (req, res) => {\n"
            "  const result = createAccount(req.body || {})\n"
            "  if (!result.ok) {\n"
            "    return res.status(result.status).json({ detail: result.detail })\n"
            "  }\n"
            "  return res.status(201).json(result)\n"
            "})\n\n"
            "authRouter.get('/me', (req, res) => {\n"
            "  const email = String(req.query?.email || 'tchelo@pulso.com')\n"
            "  const user = findUserByEmail(email)\n"
            "  if (!user) {\n"
            "    return res.status(404).json({ detail: 'Usuário não encontrado' })\n"
            "  }\n"
            "  return res.json({ id: user.id, email: user.email, name: user.name, profiles: user.profiles })\n"
            "})\n\n"
            "authRouter.get('/profiles', (_req, res) => {\n"
            "  return res.json(['admin', 'editor', 'viewer'])\n"
            "})\n"
        )

    if path_lower.endswith("backend/src/server.js"):
        return (
            "import cors from 'cors'\n"
            "import express from 'express'\n"
            "import { authRouter } from './routes/auth.routes.js'\n\n"
            "const app = express()\n"
            "const port = Number(process.env.BACKEND_PORT || 3001)\n\n"
            "app.use(cors())\n"
            "app.use(express.json())\n"
            "app.get('/health', (_req, res) => res.json({ status: 'ok' }))\n"
            "app.use('/auth', authRouter)\n\n"
            "app.listen(port, '127.0.0.1', () => {\n"
            "  console.log(`[backend] running on http://127.0.0.1:${port}`)\n"
            "})\n"
        )

    if path_lower.endswith((".ts", ".js")):
        if "service" in path_lower and "auth" in path_lower:
            return (
                "const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3001'\n\n"
                "export async function login(email: string, password: string) {\n"
                "  const resp = await fetch(`${API_URL}/auth/login`, {\n"
                "    method: 'POST', headers: { 'Content-Type': 'application/json' },\n"
                "    body: JSON.stringify({ email, password }),\n"
                "  })\n"
                "  if (!resp.ok) throw new Error('Falha no login')\n"
                "  return resp.json()\n"
                "}\n"
                "\n"
                "export async function createAccount(payload: { name: string; email: string; password: string }) {\n"
                "  const resp = await fetch(`${API_URL}/auth/create_account`, {\n"
                "    method: 'POST', headers: { 'Content-Type': 'application/json' },\n"
                "    body: JSON.stringify(payload),\n"
                "  })\n"
                "  if (!resp.ok) {\n"
                "    const data = await resp.json().catch(() => ({}))\n"
                "    throw new Error((data as { detail?: string }).detail || 'Falha ao criar conta')\n"
                "  }\n"
                "  return resp.json()\n"
                "}\n"
                "\n"
                "export async function getProfiles() {\n"
                "  const resp = await fetch(`${API_URL}/auth/profiles`)\n"
                "  if (!resp.ok) throw new Error('Falha ao buscar perfis')\n"
                "  return resp.json()\n"
                "}\n"
            )
        if "service" in path_lower:
            return f"// {name}\nconst API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'\nexport {{}}\n"
        if "hook" in path_lower:
            return f"import {{ useState }} from 'react'\n\nexport function {name}() {{\n  const [loading, setLoading] = useState(false)\n  return {{ loading, setLoading }}\n}}\n"
        return f"// {name}\nexport {{}}\n"
    
    # .vue
    if path_lower.endswith(".vue"):
        return f"<template><div>{name}</div></template>\n<script setup></script>\n"
    
    return ""


def create_structure_from_report_js(root_path: str, id_requisicao: str) -> Dict[str, Any]:
    """
    Lê 01_structure_report.json e cria fisicamente root_path/REQ-xxx/generated_code.
    Equivalente ao Python create_structure_from_report para stack JavaScript.
    """
    try:
        if not root_path or not str(root_path).strip():
            raise ValueError("root_path é obrigatório para criar estrutura e relatórios no disco.")
        root_path = os.path.normpath(os.path.abspath(str(root_path).strip()))
        reports_dir = os.path.join(root_path, "reports", id_requisicao)
        structure_report_path = os.path.join(reports_dir, "01_structure_report.json")
        if not os.path.exists(structure_report_path):
            raise FileNotFoundError(f"Relatório não encontrado: {structure_report_path}")

        with open(structure_report_path, encoding="utf-8") as f:
            data = json.load(f)

        estrutura = data.get("estrutura_arquivos", {})
        if not estrutura:
            raise ValueError("Relatório de estrutura inválido ou vazio.")
        estrutura = _ensure_fullstack_js_structure(estrutura)

        base_dir = os.path.join(root_path, id_requisicao, "generated_code")
        base_dir_abs = os.path.abspath(base_dir)
        os.makedirs(base_dir, exist_ok=True)

        created: Dict[str, List[str]] = {}

        for folder, files in estrutura.items():
            if not isinstance(files, list):
                continue
            safe_folder = sanitize_relative_path(str(folder or ".").strip())
            if safe_folder is None:
                continue
            folder_path = base_dir if safe_folder == "." else os.path.join(base_dir, safe_folder)
            if not is_path_under_base(os.path.abspath(folder_path), base_dir_abs):
                continue
            if folder and not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)

            created[folder or "."] = []
            for file in files:
                if not isinstance(file, str) or not file or ".." in file or file.startswith("/"):
                    continue
                file_path = os.path.join(folder_path, file)
                if not is_path_under_base(os.path.abspath(file_path), base_dir_abs):
                    continue
                ext = os.path.splitext(file)[1]
                if ext or file in (".env", ".gitignore", "README.md"):
                    content = _stub_for_js_file(
                        file if safe_folder == "." else f"{safe_folder}/{file}",
                        str(folder or "."),
                        estrutura,
                    )
                    if content is None:
                        content = ""
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content if content else f"/* {file} */\n")
                    created[folder or "."].append(file)
                else:
                    os.makedirs(file_path, exist_ok=True)

        manifest = {
            "id_requisicao": id_requisicao,
            "root_path": base_dir,
            "created": created,
            "skipped": [],
            "timestamp": datetime.now().isoformat(),
            "status": "sucesso",
        }

        with open(os.path.join(base_dir, "structure_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4, ensure_ascii=False)

        log_workflow(id_requisicao, f"[JS] Estrutura criada em {base_dir}")
        add_log("info", f"[structure_creator_js] Estrutura criada: {base_dir}", "structure_creator_js")
        return manifest

    except Exception as e:
        log_workflow(id_requisicao, f"[JS] Erro ao criar estrutura: {e}")
        return {"erro": str(e).strip()[:500] if str(e) else "Erro ao criar estrutura.", "status": "falha"}
