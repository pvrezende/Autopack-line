import { useState } from 'react'
import type { Product, ProductionLine } from '../types/domain'
import { OeeHistoryPanel } from './OeeHistoryPanel'
import { LossAnalysisPanel } from './LossAnalysisPanel'
import { OperationalAlertsPanel } from './OperationalAlertsPanel'
import { AlertTrendPanel } from './AlertTrendPanel'
import { ExecutiveIndicatorsPanel } from './ExecutiveIndicatorsPanel'
import { CoreValidationPanel } from './CoreValidationPanel'

type Props = { products: Product[]; lines: ProductionLine[]; refreshKey: number }
type IndicatorTab = 'oee' | 'losses' | 'alerts' | 'trend' | 'executive' | 'validation'

export function IndicatorsPanel(props: Props) {
  const [tab, setTab] = useState<IndicatorTab>('oee')
  return <div className="indicators-container">
    <div className="indicator-tabs" role="tablist" aria-label="Indicadores">
      <button className={tab === 'oee' ? 'active' : ''} onClick={() => setTab('oee')}>Histórico de OEE</button>
      <button className={tab === 'losses' ? 'active' : ''} onClick={() => setTab('losses')}>Análise de perdas</button>
      <button className={tab === 'alerts' ? 'active' : ''} onClick={() => setTab('alerts')}>Alertas operacionais</button>
      <button className={tab === 'trend' ? 'active' : ''} onClick={() => setTab('trend')}>Tendência dos alertas</button>
      <button className={tab === 'executive' ? 'active' : ''} onClick={() => setTab('executive')}>Resumo executivo</button>
      <button className={tab === 'validation' ? 'active' : ''} onClick={() => setTab('validation')}>Validação do núcleo</button>
    </div>
    {tab === 'oee' && <OeeHistoryPanel {...props} />}
    {tab === 'losses' && <LossAnalysisPanel {...props} />}
    {tab === 'alerts' && <OperationalAlertsPanel {...props} />}
    {tab === 'trend' && <AlertTrendPanel {...props} />}
    {tab === 'executive' && <ExecutiveIndicatorsPanel {...props} />}
    {tab === 'validation' && <CoreValidationPanel {...props} />}
  </div>
}
