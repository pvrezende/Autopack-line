import { FormEvent, useEffect, useMemo, useState } from 'react'
import { createLine, createProduct, listIndicatorThresholds, setIndicatorThreshold, setPalletConfig, setProductionTarget, updateProduct } from '../services/api'
import type { IndicatorThreshold, PalletConfig, Product, ProductionLine, ProductionTarget } from '../types/domain'

type Props = {
  products: Product[]
  lines: ProductionLine[]
  configs: PalletConfig[]
  targets: ProductionTarget[]
  onChanged: () => Promise<void>
}

export function ConfigurationPanel({ products, lines, configs, targets, onChanged }: Props) {
  const [message, setMessage] = useState('')
  const [configPage, setConfigPage] = useState(1)
  const [targetPage, setTargetPage] = useState(1)
  const [openPanel, setOpenPanel] = useState<'product' | 'recipe' | 'line' | 'pallet' | 'target' | 'alerts' | 'alertconfigs' | 'targets' | 'configs'>('target')
  const configPageSize = 5
  const targetPageSize = 5
  const [productForm, setProductForm] = useState({
    sku: '', ean: '', model: '', name: '', capacity_btu: '', plc_recipe_id: '', plc_recipe_released: false, active: true,
  })
  const [recipeForm, setRecipeForm] = useState({ product_id: '', plc_recipe_id: '', plc_recipe_released: false })
  const [lineForm, setLineForm] = useState({ code: '', name: '', description: '', active: true })
  const [configForm, setConfigForm] = useState({ product_id: '', line_id: '', max_boxes: '' })
  const [targetForm, setTargetForm] = useState({ line_id: '', product_id: '', hourly_target: '', daily_target: '', takt_seconds: '' })

  const [thresholds, setThresholds] = useState<IndicatorThreshold[]>([])
  const [alertPage, setAlertPage] = useState(1)
  const alertPageSize = 5
  const [alertForm, setAlertForm] = useState({
    line_id: '', product_id: '',
    availability_warning: '', availability_critical: '',
    performance_warning: '', performance_critical: '',
    quality_warning: '', quality_critical: '',
    oee_warning: '', oee_critical: '',
  })

  function updateHourlyTarget(value: string) {
    const hourly = Number(value)
    const takt = value && Number.isFinite(hourly) && hourly > 0 ? (3600 / hourly).toFixed(2) : ''
    setTargetForm((current) => ({ ...current, hourly_target: value, takt_seconds: takt }))
  }

  const activeConfigs = useMemo(() => configs.filter((item) => item.active && !item.valid_until), [configs])
  const activeTargets = useMemo(() => targets.filter((item) => item.active && !item.valid_until), [targets])
  const activeThresholds = useMemo(() => thresholds.filter((item) => item.active && !item.valid_until), [thresholds])
  const alertTotalPages = Math.max(1, Math.ceil(activeThresholds.length / alertPageSize))
  const visibleThresholds = activeThresholds.slice((alertPage - 1) * alertPageSize, alertPage * alertPageSize)
  useEffect(() => { listIndicatorThresholds().then(setThresholds).catch(() => undefined) }, [])
  useEffect(() => { if (alertPage > alertTotalPages) setAlertPage(alertTotalPages) }, [alertPage, alertTotalPages])
  const configTotalPages = Math.max(1, Math.ceil(activeConfigs.length / configPageSize))
  const targetTotalPages = Math.max(1, Math.ceil(activeTargets.length / targetPageSize))
  const visibleConfigs = activeConfigs.slice((configPage - 1) * configPageSize, configPage * configPageSize)
  const visibleTargets = activeTargets.slice((targetPage - 1) * targetPageSize, targetPage * targetPageSize)
  useEffect(() => { if (configPage > configTotalPages) setConfigPage(configTotalPages) }, [configPage, configTotalPages])
  useEffect(() => { if (targetPage > targetTotalPages) setTargetPage(targetTotalPages) }, [targetPage, targetTotalPages])

  async function handleProduct(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      await createProduct({
        sku: productForm.sku.trim(),
        ean: productForm.ean.trim() || null,
        model: productForm.model.trim(),
        name: productForm.name.trim(),
        capacity_btu: productForm.capacity_btu ? Number(productForm.capacity_btu) : null,
        plc_recipe_id: productForm.plc_recipe_id ? Number(productForm.plc_recipe_id) : null,
        plc_recipe_released: productForm.plc_recipe_released,
        active: true,
      })
      setProductForm({ sku: '', ean: '', model: '', name: '', capacity_btu: '', plc_recipe_id: '', plc_recipe_released: false, active: true })
      setMessage('Produto cadastrado.')
      await onChanged()
    } catch (error) { setMessage((error as Error).message) }
  }

  async function handleRecipe(event: FormEvent) {
    event.preventDefault(); setMessage('')
    try {
      await updateProduct(Number(recipeForm.product_id), {
        plc_recipe_id: recipeForm.plc_recipe_id ? Number(recipeForm.plc_recipe_id) : null,
        plc_recipe_released: recipeForm.plc_recipe_released,
      })
      setMessage('Receita Modbus do produto atualizada.')
      await onChanged()
    } catch (error) { setMessage((error as Error).message) }
  }

  async function handleLine(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      await createLine({ ...lineForm, description: lineForm.description || null, active: true })
      setLineForm({ code: '', name: '', description: '', active: true })
      setMessage('Linha cadastrada.')
      await onChanged()
    } catch (error) { setMessage((error as Error).message) }
  }

  async function handleConfig(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      await setPalletConfig({
        product_id: Number(configForm.product_id), line_id: Number(configForm.line_id), max_boxes: Number(configForm.max_boxes),
      })
      setMessage('Quantidade por palete atualizada. A alteração vale para novos paletes.')
      await onChanged()
    } catch (error) { setMessage((error as Error).message) }
  }

  async function handleTarget(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      await setProductionTarget({
        line_id: Number(targetForm.line_id),
        product_id: targetForm.product_id ? Number(targetForm.product_id) : null,
        hourly_target: targetForm.hourly_target ? Number(targetForm.hourly_target) : null,
        daily_target: targetForm.daily_target ? Number(targetForm.daily_target) : null,
        takt_seconds: targetForm.takt_seconds ? Number(targetForm.takt_seconds) : null,
      })
      setMessage('Meta registrada.')
      await onChanged()
    } catch (error) { setMessage((error as Error).message) }
  }

  async function handleAlertThreshold(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      await setIndicatorThreshold({
        line_id: Number(alertForm.line_id),
        product_id: alertForm.product_id ? Number(alertForm.product_id) : null,
        availability_warning: Number(alertForm.availability_warning),
        availability_critical: Number(alertForm.availability_critical),
        performance_warning: Number(alertForm.performance_warning),
        performance_critical: Number(alertForm.performance_critical),
        quality_warning: Number(alertForm.quality_warning),
        quality_critical: Number(alertForm.quality_critical),
        oee_warning: Number(alertForm.oee_warning),
        oee_critical: Number(alertForm.oee_critical),
      })
      setMessage('Limites de indicadores registrados.')
      setThresholds(await listIndicatorThresholds())
      await onChanged()
    } catch (error) { setMessage((error as Error).message) }
  }

  return (
    <section className="card-section">
      <div className="section-heading">
        <div><p className="eyebrow">CONFIGURAÇÕES</p><h2>Parâmetros editáveis</h2></div>
        <span className="badge">sem valores fixos no código</span>
      </div>
      {message && <div className="message">{message}</div>}
      <div className="configuration-accordion">
        <button type="button" className={`config-toggle ${openPanel === 'product' ? 'active' : ''}`} onClick={() => setOpenPanel(openPanel === 'product' ? 'target' : 'product')}><span className="config-hamburger">☰</span><span><strong>Novo produto</strong><small>Cadastrar SKU, EAN, modelo, nome e capacidade</small></span><b>{openPanel === 'product' ? '−' : '+'}</b></button>
        {openPanel === 'product' && <form className="form-card config-collapsible" onSubmit={handleProduct}>
          <label>SKU<input required value={productForm.sku} onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })} /></label>
          <label>EAN<input value={productForm.ean} onChange={(e) => setProductForm({ ...productForm, ean: e.target.value })} /></label>
          <label>Modelo<input required value={productForm.model} onChange={(e) => setProductForm({ ...productForm, model: e.target.value })} /></label>
          <label>Nome<input required value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} /></label>
          <label>Capacidade BTU<input type="number" min="1" value={productForm.capacity_btu} onChange={(e) => setProductForm({ ...productForm, capacity_btu: e.target.value })} /></label>
          <label>Receita CLP<select value={productForm.plc_recipe_id} onChange={(e) => setProductForm({ ...productForm, plc_recipe_id: e.target.value })}><option value="">Não configurada</option>{[1,2,3,4,5,6,7,8].map(id => <option key={id} value={id}>Receita {id}</option>)}</select></label>
          <label className="check"><input type="checkbox" checked={productForm.plc_recipe_released} onChange={(e) => setProductForm({ ...productForm, plc_recipe_released: e.target.checked })} />Receita liberada fisicamente</label>
          <button type="submit">Cadastrar produto</button>
        </form>}

        <button type="button" className={`config-toggle ${openPanel === 'recipe' ? 'active' : ''}`} onClick={() => setOpenPanel(openPanel === 'recipe' ? 'target' : 'recipe')}><span className="config-hamburger">☰</span><span><strong>Receita Modbus do produto</strong><small>Vincular ID 1–8 e controlar a liberação física</small></span><b>{openPanel === 'recipe' ? '−' : '+'}</b></button>
        {openPanel === 'recipe' && <form className="form-card config-collapsible" onSubmit={handleRecipe}>
          <label>Produto<select required value={recipeForm.product_id} onChange={(e) => { const product = products.find(item => item.id === Number(e.target.value)); setRecipeForm({ product_id:e.target.value, plc_recipe_id:product?.plc_recipe_id ? String(product.plc_recipe_id) : '', plc_recipe_released:Boolean(product?.plc_recipe_released) }) }}><option value="">Selecione</option>{products.map(item => <option key={item.id} value={item.id}>{item.model} · {item.name}</option>)}</select></label>
          <label>Receita CLP<select value={recipeForm.plc_recipe_id} onChange={(e) => setRecipeForm({ ...recipeForm, plc_recipe_id:e.target.value })}><option value="">Não configurada</option>{[1,2,3,4,5,6,7,8].map(id => <option key={id} value={id}>Receita {id}</option>)}</select></label>
          <label className="check"><input type="checkbox" checked={recipeForm.plc_recipe_released} onChange={(e) => setRecipeForm({ ...recipeForm, plc_recipe_released:e.target.checked })} />Liberada para envio ao CLP</label>
          <button type="submit">Salvar receita</button>
        </form>}

        <button type="button" className={`config-toggle ${openPanel === 'line' ? 'active' : ''}`} onClick={() => setOpenPanel(openPanel === 'line' ? 'target' : 'line')}><span className="config-hamburger">☰</span><span><strong>Nova linha</strong><small>Cadastrar código, nome e descrição da linha</small></span><b>{openPanel === 'line' ? '−' : '+'}</b></button>
        {openPanel === 'line' && <form className="form-card config-collapsible" onSubmit={handleLine}>
          <label>Código<input required placeholder="L01" value={lineForm.code} onChange={(e) => setLineForm({ ...lineForm, code: e.target.value })} /></label>
          <label>Nome<input required placeholder="Linha 1" value={lineForm.name} onChange={(e) => setLineForm({ ...lineForm, name: e.target.value })} /></label>
          <label>Descrição<input value={lineForm.description} onChange={(e) => setLineForm({ ...lineForm, description: e.target.value })} /></label>
          <button type="submit">Cadastrar linha</button>
        </form>}

        <button type="button" className={`config-toggle ${openPanel === 'pallet' ? 'active' : ''}`} onClick={() => setOpenPanel(openPanel === 'pallet' ? 'target' : 'pallet')}><span className="config-hamburger">☰</span><span><strong>Quantidade por palete</strong><small>Definir o máximo de caixas por produto e linha</small></span><b>{openPanel === 'pallet' ? '−' : '+'}</b></button>
        {openPanel === 'pallet' && <form className="form-card config-collapsible" onSubmit={handleConfig}>
          <label>Produto<select required value={configForm.product_id} onChange={(e) => setConfigForm({ ...configForm, product_id: e.target.value })}><option value="">Selecione</option>{products.map((p) => <option key={p.id} value={p.id}>{p.model} · {p.ean ?? p.sku}</option>)}</select></label>
          <label>Linha<select required value={configForm.line_id} onChange={(e) => setConfigForm({ ...configForm, line_id: e.target.value })}><option value="">Selecione</option>{lines.map((l) => <option key={l.id} value={l.id}>{l.code} · {l.name}</option>)}</select></label>
          <label>Máximo de caixas<input required type="number" min="1" max="10000" value={configForm.max_boxes} onChange={(e) => setConfigForm({ ...configForm, max_boxes: e.target.value })} /></label>
          <button type="submit">Salvar configuração</button>
        </form>}

        <button type="button" className={`config-toggle ${openPanel === 'target' ? 'active' : ''}`} onClick={() => setOpenPanel('target')}><span className="config-hamburger">☰</span><span><strong>Metas de produção</strong><small>Configurar meta/hora, meta diária e takt</small></span><b>{openPanel === 'target' ? '−' : '+'}</b></button>
        {openPanel === 'target' && <form className="form-card config-collapsible" onSubmit={handleTarget}>
          <label>Linha<select required value={targetForm.line_id} onChange={(e) => setTargetForm({ ...targetForm, line_id: e.target.value })}><option value="">Selecione</option>{lines.map((l) => <option key={l.id} value={l.id}>{l.code} · {l.name}</option>)}</select></label>
          <label>Produto (opcional)<select value={targetForm.product_id} onChange={(e) => setTargetForm({ ...targetForm, product_id: e.target.value })}><option value="">Meta geral da linha</option>{products.map((p) => <option key={p.id} value={p.id}>{p.model}</option>)}</select></label>
          <label>Meta/hora<input type="number" min="1" value={targetForm.hourly_target} onChange={(e) => updateHourlyTarget(e.target.value)} /></label>
          <label>Meta diária<input type="number" min="1" value={targetForm.daily_target} onChange={(e) => setTargetForm({ ...targetForm, daily_target: e.target.value })} /></label>
          <label><span className="label-with-help">Takt (s)<span className="field-help" tabIndex={0} aria-label="O que é Takt?">?<span className="field-help-tooltip"><strong>O que é Takt?</strong><small>É o ritmo necessário para atingir a meta de produção. O AUTOPACKLINE calcula automaticamente: 3600 segundos ÷ Meta/hora. Ex.: meta de 2 unidades/hora = Takt de 1800 s (1 unidade a cada 30 minutos).</small></span></span></span><input type="number" min="0.01" step="0.01" value={targetForm.takt_seconds} readOnly title="Calculado automaticamente a partir da Meta/hora" /><small className="field-note">Calculado automaticamente pela Meta/hora.</small></label>
          <button type="submit">Salvar meta</button>
        </form>}

        <button type="button" className={`config-toggle ${openPanel === 'alerts' ? 'active' : ''}`} onClick={() => setOpenPanel('alerts')}><span className="config-hamburger">☰</span><span><strong>Limites e alertas dos indicadores</strong><small>Definir faixas de atenção e crítico para Disponibilidade, Performance, Qualidade e OEE</small></span><b>{openPanel === 'alerts' ? '−' : '+'}</b></button>
        {openPanel === 'alerts' && <form className="form-card config-collapsible indicator-threshold-form" onSubmit={handleAlertThreshold}>
          <label>Linha<select required value={alertForm.line_id} onChange={(e) => setAlertForm({ ...alertForm, line_id:e.target.value })}><option value="">Selecione</option>{lines.map((l) => <option key={l.id} value={l.id}>{l.code} · {l.name}</option>)}</select></label>
          <label>Produto (opcional)<select value={alertForm.product_id} onChange={(e) => setAlertForm({ ...alertForm, product_id:e.target.value })}><option value="">Limite geral da linha</option>{products.map((p) => <option key={p.id} value={p.id}>{p.model}</option>)}</select></label>
          <div className="threshold-help"><strong>Como funciona</strong><small>Valor igual ou acima de Atenção = OK. Abaixo de Atenção = ATENÇÃO. Abaixo de Crítico = CRÍTICO. Nenhum valor é fixo no código.</small></div>
          {([['Disponibilidade','availability'],['Performance','performance'],['Qualidade','quality'],['OEE','oee']] as const).map(([label,key]) => <div className="threshold-row" key={key}><strong>{label}</strong><label>Atenção abaixo de (%)<input required type="number" min="0" max="100" step="0.1" value={alertForm[`${key}_warning`]} onChange={(e) => setAlertForm({ ...alertForm, [`${key}_warning`]:e.target.value })} /></label><label>Crítico abaixo de (%)<input required type="number" min="0" max="100" step="0.1" value={alertForm[`${key}_critical`]} onChange={(e) => setAlertForm({ ...alertForm, [`${key}_critical`]:e.target.value })} /></label></div>)}
          <button type="submit">Salvar limites</button>
        </form>}

        <button type="button" className={`config-toggle ${openPanel === 'alertconfigs' ? 'active' : ''}`} onClick={() => setOpenPanel('alertconfigs')}><span className="config-hamburger">☰</span><span><strong>Limites de indicadores ativos</strong><small>{activeThresholds.length} configuração(ões) ativa(s) · lista paginada</small></span><b>{openPanel === 'alertconfigs' ? '−' : '+'}</b></button>
        {openPanel === 'alertconfigs' && <div className="table-wrap config-collapsible"><table><thead><tr><th>Linha</th><th>Produto</th><th>Disponibilidade</th><th>Performance</th><th>Qualidade</th><th>OEE</th></tr></thead><tbody>
          {visibleThresholds.length === 0 && <tr><td colSpan={6}>Nenhum limite ativo.</td></tr>}
          {visibleThresholds.map((item) => <tr key={item.id}><td>{lines.find(l => l.id === item.line_id)?.code ?? item.line_id}</td><td>{item.product_id ? (products.find(p => p.id === item.product_id)?.model ?? item.product_id) : 'Geral da linha'}</td><td>{item.availability_warning}% / {item.availability_critical}%</td><td>{item.performance_warning}% / {item.performance_critical}%</td><td>{item.quality_warning}% / {item.quality_critical}%</td><td>{item.oee_warning}% / {item.oee_critical}%</td></tr>)}
        </tbody></table><div className="panel-pager"><span>{activeThresholds.length} configuração(ões)</span><div><button className="secondary small" disabled={alertPage <= 1} onClick={() => setAlertPage(p => p - 1)}>Anterior</button><strong>Página {alertPage} de {alertTotalPages}</strong><button className="secondary small" disabled={alertPage >= alertTotalPages} onClick={() => setAlertPage(p => p + 1)}>Próxima</button></div></div></div>}

        <button type="button" className={`config-toggle ${openPanel === 'targets' ? 'active' : ''}`} onClick={() => setOpenPanel('targets')}><span className="config-hamburger">☰</span><span><strong>Metas de produção ativas</strong><small>{activeTargets.length} meta(s) ativa(s) · lista paginada</small></span><b>{openPanel === 'targets' ? '−' : '+'}</b></button>
        {openPanel === 'targets' && <div className="table-wrap config-collapsible"><table><thead><tr><th>Linha</th><th>Produto</th><th>Meta/hora</th><th>Meta diária</th><th>Takt</th></tr></thead><tbody>
          {activeTargets.length === 0 && <tr><td colSpan={5}>Nenhuma meta ativa.</td></tr>}
          {visibleTargets.map((target) => <tr key={target.id}><td>{lines.find((l) => l.id === target.line_id)?.code ?? target.line_id}</td><td>{target.product_id ? (products.find((p) => p.id === target.product_id)?.model ?? target.product_id) : 'Geral da linha'}</td><td>{target.hourly_target ?? '—'}</td><td>{target.daily_target ?? '—'}</td><td>{target.takt_seconds != null ? `${Number(target.takt_seconds).toFixed(2)} s` : '—'}</td></tr>)}
        </tbody></table><div className="panel-pager"><span>{activeTargets.length} meta(s) ativa(s)</span><div><button className="secondary small" disabled={targetPage <= 1} onClick={() => setTargetPage(p => p - 1)}>Anterior</button><strong>Página {targetPage} de {targetTotalPages}</strong><button className="secondary small" disabled={targetPage >= targetTotalPages} onClick={() => setTargetPage(p => p + 1)}>Próxima</button></div></div></div>}

        <button type="button" className={`config-toggle ${openPanel === 'configs' ? 'active' : ''}`} onClick={() => setOpenPanel('configs')}><span className="config-hamburger">☰</span><span><strong>Configurações de palete ativas</strong><small>{activeConfigs.length} configuração(ões) · lista paginada</small></span><b>{openPanel === 'configs' ? '−' : '+'}</b></button>
        {openPanel === 'configs' && <div className="table-wrap config-collapsible"><table><thead><tr><th>Produto</th><th>Linha</th><th>Máximo</th></tr></thead><tbody>
          {activeConfigs.length === 0 && <tr><td colSpan={3}>Nenhuma configuração ativa.</td></tr>}
          {visibleConfigs.map((cfg) => <tr key={cfg.id}><td>{products.find((p) => p.id === cfg.product_id)?.model ?? cfg.product_id}</td><td>{lines.find((l) => l.id === cfg.line_id)?.code ?? cfg.line_id}</td><td>{cfg.max_boxes}</td></tr>)}
        </tbody></table><div className="panel-pager"><span>{activeConfigs.length} configuração(ões)</span><div><button className="secondary small" disabled={configPage <= 1} onClick={() => setConfigPage(p => p - 1)}>Anterior</button><strong>Página {configPage} de {configTotalPages}</strong><button className="secondary small" disabled={configPage >= configTotalPages} onClick={() => setConfigPage(p => p + 1)}>Próxima</button></div></div></div>}
      </div>
    </section>
  )
}
