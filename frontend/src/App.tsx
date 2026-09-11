import { useCallback, useEffect, useRef, useState } from 'react'
import { ConfigurationPanel } from './components/ConfigurationPanel'
import { DashboardPanel } from './components/DashboardPanel'
import { LoginPanel } from './components/LoginPanel'
import { OperationPanel } from './components/OperationPanel'
import { IndicatorsPanel } from './components/IndicatorsPanel'
import { ProductionOrdersPanel } from './components/ProductionOrdersPanel'
import { PasswordModal } from './components/PasswordModal'
import { StatusCards } from './components/StatusCards'
import { TraceabilityPanel, type TraceabilityPreset } from './components/TraceabilityPanel'
import { UserManagementPanel } from './components/UserManagementPanel'
import { WorkSchedulePanel } from './components/WorkSchedulePanel'
import {
  clearStoredToken,
  getDbHealth,
  getHealth,
  getMe,
  getStoredToken,
  listLines,
  listPalletConfigs,
  listProducts,
  listProductionTargets,
} from './services/api'
import type { PalletConfig, Product, ProductionLine, ProductionTarget, UserAccount } from './types/domain'

type Tab = 'dashboard' | 'indicators' | 'operation' | 'orders' | 'schedule' | 'configuration' | 'traceability' | 'diagnostics' | 'users'

export function App() {
  const [user, setUser] = useState<UserAccount | null>(null)
  const [authChecking, setAuthChecking] = useState(true)
  const [tab, setTab] = useState<Tab>('dashboard')
  const [backendStatus, setBackendStatus] = useState('verificando...')
  const [dbStatus, setDbStatus] = useState('verificando...')
  const [products, setProducts] = useState<Product[]>([])
  const [lines, setLines] = useState<ProductionLine[]>([])
  const [configs, setConfigs] = useState<PalletConfig[]>([])
  const [targets, setTargets] = useState<ProductionTarget[]>([])
  const [traceRefreshKey, setTraceRefreshKey] = useState(0)
  const [dashboardRefreshKey, setDashboardRefreshKey] = useState(0)
  const [operationRefreshKey, setOperationRefreshKey] = useState(0)
  const [tracePreset, setTracePreset] = useState<TraceabilityPreset | null>(null)
  const [tracePresetKey, setTracePresetKey] = useState(0)
  const [loadError, setLoadError] = useState('')
  const [passwordOpen, setPasswordOpen] = useState(false)
  const [sidebarVisible, setSidebarVisible] = useState(() => typeof window !== 'undefined' ? window.innerWidth > 980 : true)
  const sidebarTimerRef = useRef<number | null>(null)

  const canTrace = user?.role === 'SUPERVISOR' || user?.role === 'ADMIN'
  const canManageProduction = user?.role === 'SUPERVISOR' || user?.role === 'ADMIN'
  const isAdmin = user?.role === 'ADMIN'

  const logout = useCallback(() => {
    clearStoredToken(); setUser(null); setProducts([]); setLines([]); setConfigs([]); setTargets([]); setTab('dashboard'); setLoadError('')
  }, [])

  useEffect(() => {
    const onUnauthorized = () => logout()
    window.addEventListener('autopackline:unauthorized', onUnauthorized)
    if (!getStoredToken()) { setAuthChecking(false); return () => window.removeEventListener('autopackline:unauthorized', onUnauthorized) }
    getMe().then(setUser).catch(logout).finally(() => setAuthChecking(false))
    return () => window.removeEventListener('autopackline:unauthorized', onUnauthorized)
  }, [logout])

  const refresh = useCallback(async () => {
    if (!user) return
    try {
      const [productData, lineData, configData, targetData] = await Promise.all([
        listProducts(), listLines(), listPalletConfigs(), listProductionTargets(),
      ])
      setProducts(productData); setLines(lineData); setConfigs(configData); setTargets(targetData)
      setTraceRefreshKey(v => v + 1); setDashboardRefreshKey(v => v + 1); setOperationRefreshKey(v => v + 1); setLoadError('')
    } catch (error) { setLoadError((error as Error).message) }
  }, [user])

  useEffect(() => {
    if (!user) return
    getHealth().then(() => setBackendStatus('online')).catch(() => setBackendStatus('offline'))
    getDbHealth().then(() => setDbStatus('online')).catch(() => setDbStatus('offline'))
    refresh()
  }, [user, refresh])

  const scheduleSidebarHide = useCallback(() => {
    if (!user || window.innerWidth <= 980) return
    if (sidebarTimerRef.current !== null) window.clearTimeout(sidebarTimerRef.current)
    sidebarTimerRef.current = window.setTimeout(() => setSidebarVisible(false), 5000)
  }, [user])

  useEffect(() => {
    if (!user) return

    // Desktop: mantém o comportamento de painel, revelando o menu por atividade
    // e recolhendo após 5 s. Mobile/tablet: o menu é controlado SOMENTE
    // pelo hambúrguer para evitar abrir/fechar a cada toque durante a leitura.
    const handleActivity = () => {
      if (window.innerWidth <= 980) return
      setSidebarVisible(true)
      scheduleSidebarHide()
    }

    const handleResize = () => {
      if (sidebarTimerRef.current !== null) {
        window.clearTimeout(sidebarTimerRef.current)
        sidebarTimerRef.current = null
      }
      if (window.innerWidth <= 980) {
        setSidebarVisible(false)
        return
      }
      setSidebarVisible(true)
      scheduleSidebarHide()
    }

    window.addEventListener('mousemove', handleActivity, { passive: true })
    window.addEventListener('keydown', handleActivity)
    window.addEventListener('resize', handleResize)

    if (window.innerWidth <= 980) setSidebarVisible(false)
    else scheduleSidebarHide()

    return () => {
      window.removeEventListener('mousemove', handleActivity)
      window.removeEventListener('keydown', handleActivity)
      window.removeEventListener('resize', handleResize)
      if (sidebarTimerRef.current !== null) window.clearTimeout(sidebarTimerRef.current)
    }
  }, [user, scheduleSidebarHide])

  const toggleSidebar = () => setSidebarVisible(visible => {
    const next = !visible
    if (window.innerWidth > 980) {
      if (next) scheduleSidebarHide()
      else if (sidebarTimerRef.current !== null) window.clearTimeout(sidebarTimerRef.current)
    }
    return next
  })

  function openTraceability(preset: TraceabilityPreset) {
    if (!canTrace) return
    setTracePreset(preset); setTracePresetKey(v => v + 1); setTab('traceability')
  }

  if (authChecking) return <div className="login-page"><div className="login-card"><strong>AUTOPACKLINE</strong><p>Validando sessão...</p></div></div>
  if (!user) return <LoginPanel onLogin={(loggedUser) => { setUser(loggedUser); setAuthChecking(false) }} />

  return <div className={`app-shell ${sidebarVisible ? 'sidebar-visible' : 'sidebar-hidden'}`}>
    <button className="sidebar-toggle" onClick={toggleSidebar} aria-label={sidebarVisible ? 'Ocultar menu' : 'Mostrar menu'} title={sidebarVisible ? 'Ocultar menu' : 'Mostrar menu'}><span></span><span></span><span></span></button>
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">A</span><div><strong>AUTOPACKLINE</strong><small>Rastreabilidade industrial</small></div></div>
      <nav>
        <button className={tab === 'dashboard' ? 'active' : ''} onClick={() => setTab('dashboard')}>Dashboard</button>
        {canTrace && <button className={tab === 'indicators' ? 'active' : ''} onClick={() => setTab('indicators')}>Indicadores</button>}
        <button className={tab === 'operation' ? 'active' : ''} onClick={() => setTab('operation')}>Operação</button>
        {canManageProduction && <button className={tab === 'orders' ? 'active' : ''} onClick={() => setTab('orders')}>Ordens de Produção</button>}
        {canTrace && <button className={tab === 'schedule' ? 'active' : ''} onClick={() => setTab('schedule')}>Jornada e Paradas</button>}
        {isAdmin && <button className={tab === 'configuration' ? 'active' : ''} onClick={() => setTab('configuration')}>Configurações</button>}
        {canTrace && <button className={tab === 'traceability' ? 'active' : ''} onClick={() => setTab('traceability')}>Rastreabilidade</button>}
        {canTrace && <button className={tab === 'diagnostics' ? 'active' : ''} onClick={() => setTab('diagnostics')}>Manutenção e Diagnóstico</button>}
        {isAdmin && <button className={tab === 'users' ? 'active' : ''} onClick={() => setTab('users')}>Usuários</button>}
      </nav>
      <div className="sidebar-user"><strong>{user.full_name}</strong><span>{user.role === 'ADMIN' ? 'Administrador' : user.role === 'SUPERVISOR' ? 'Supervisor' : 'Operador'}</span><button onClick={() => setPasswordOpen(true)}>Alterar senha</button><button onClick={logout}>Sair</button></div>
    </aside>

    <main className={`content-shell ${tab}-view ${tab === 'dashboard' ? 'dashboard-view' : ''}`}>
      <header className="topbar"><div><p className="eyebrow">RASTREABILIDADE INDUSTRIAL</p><h1>AUTOPACKLINE</h1></div><div className="topbar-actions"><div className="current-user"><strong>{user.full_name}</strong><span>{user.role}</span></div><button className="secondary small" onClick={refresh}>Atualizar dados</button><button className="secondary small" onClick={logout}>Sair</button><button className="stage-help" aria-label="Ajuda rápida" title="Ajuda rápida"><span>?</span><div className="stage-tooltip"><strong>AJUDA RÁPIDA</strong><small>Acompanhe a produção no Dashboard e realize as leituras na Operação. Informações técnicas ficam separadas em Manutenção e Diagnóstico.</small></div></button></div></header>
      {tab === 'diagnostics' && <StatusCards backendStatus={backendStatus} dbStatus={dbStatus} />}
      {loadError && <div className="message error">{loadError}</div>}
      {tab === 'dashboard' && <DashboardPanel products={products} lines={lines} refreshKey={dashboardRefreshKey} onOpenTraceability={openTraceability} canTraceability={canTrace} />}
      {tab === 'indicators' && canTrace && <IndicatorsPanel products={products} lines={lines} refreshKey={dashboardRefreshKey} />}
      {tab === 'operation' && <OperationPanel lines={lines} onChanged={refresh} refreshKey={operationRefreshKey} view="operation" />}
      {tab === 'orders' && canManageProduction && <ProductionOrdersPanel products={products} lines={lines} user={user} onChanged={refresh} />}
      {tab === 'schedule' && canTrace && <WorkSchedulePanel lines={lines} user={user} />}
      {tab === 'configuration' && isAdmin && <ConfigurationPanel products={products} lines={lines} configs={configs} targets={targets} onChanged={refresh} />}
      {tab === 'traceability' && canTrace && <TraceabilityPanel products={products} lines={lines} refreshKey={traceRefreshKey} preset={tracePreset} presetKey={tracePresetKey} />}
      {tab === 'diagnostics' && canTrace && <OperationPanel lines={lines} onChanged={refresh} refreshKey={operationRefreshKey} view="diagnostics" />}
      {tab === 'users' && isAdmin && <UserManagementPanel currentUser={user} />}
    </main>
    {passwordOpen && <PasswordModal onClose={() => setPasswordOpen(false)} />}
  </div>
}
