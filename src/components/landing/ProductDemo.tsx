import { useRef, useState } from 'react';
import Icon from './Icon';
import styles from './landing.module.css';

const tabs = [
  { label: 'Análise da petição', icon: 'document' as const },
  { label: 'Chat com o caso', icon: 'chat' as const },
  { label: 'Minuta em Word', icon: 'download' as const },
];

export default function ProductDemo() {
  const [active, setActive] = useState(0);
  const refs = useRef<Array<HTMLButtonElement | null>>([]);

  return (
    <div className={styles.demo}>
      <div className={styles.demoChrome}>
        <span className={styles.windowDots} aria-hidden="true"><i /><i /><i /></span>
        <span>Seu espaço de trabalho</span>
        <span className={styles.demoBadge}><span /> Exemplo ilustrativo</span>
      </div>
      <div className={styles.demoBody}>
        <aside className={styles.demoSidebar} aria-label="Etapas da demonstração">
          <span className={styles.demoBrand}><Icon name="scale" /> SmartLawer</span>
          <span className={styles.demoEyebrow}>DO DOCUMENTO À ESTRATÉGIA</span>
          <div role="tablist" aria-label="Conheça os recursos" aria-orientation="vertical" className={styles.demoTabs}>
            {tabs.map((tab, index) => (
              <button key={tab.label} ref={(element) => { refs.current[index] = element; }} type="button" role="tab" id={`demo-tab-${index}`} aria-selected={active === index} aria-controls={`demo-panel-${index}`} tabIndex={active === index ? 0 : -1} onClick={() => setActive(index)} onKeyDown={(event) => {
                if (!['ArrowDown', 'ArrowUp', 'ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
                event.preventDefault();
                const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (['ArrowDown', 'ArrowRight'].includes(event.key) ? 1 : -1) + tabs.length) % tabs.length;
                setActive(next);
                refs.current[next]?.focus();
              }}><Icon name={tab.icon} size={18} /><span>{tab.label}</span><span className={styles.tabArrow}>↗</span></button>
            ))}
          </div>
          <div className={styles.demoSidebarNote}><Icon name="shield" size={18} /><p>A IA organiza.<br /><strong>Você decide.</strong></p></div>
        </aside>
        <div className={styles.demoMain}>
          <div className={styles.demoFile}><span><Icon name="document" size={16} /> petição_inicial.pdf</span><span className={styles.reviewBadge}>Rascunho para revisão</span></div>
          <div hidden={active !== 0} role="tabpanel" id="demo-panel-0" aria-labelledby="demo-tab-0" tabIndex={0} className={styles.demoPanel}>
            <span className={styles.demoEyebrow}>VISÃO GERAL DO CASO</span>
            <h3>Clareza para o próximo passo.</h3>
            <p>Os pontos da petição, organizados para a sua leitura crítica.</p>
            <div className={styles.demoSummary}><span className={styles.demoSummaryIcon}><Icon name="spark" /></span><div><strong>Resumo dos fatos</strong><p>A parte autora relata divergências na execução do contrato e solicita reparação pelos prejuízos alegados.</p></div></div>
            <div className={styles.demoColumns}><div><span>01 / PEDIDOS IDENTIFICADOS</span><p>Rescisão contratual</p><p>Restituição de valores</p></div><div><span>02 / PONTOS PARA A DEFESA</span><p>Conferir a prova documental</p><p>Avaliar o nexo entre fato e dano</p></div></div>
            <div className={styles.demoBottom}><Icon name="check" size={15} /> Uma visão organizada para aprofundar sua análise.</div>
          </div>
          <div hidden={active !== 1} role="tabpanel" id="demo-panel-1" aria-labelledby="demo-tab-1" tabIndex={0} className={styles.demoPanel}>
            <span className={styles.demoEyebrow}>CONVERSE COM SEUS DOCUMENTOS</span>
            <h3>Uma pergunta. Mais contexto.</h3>
            <div className={styles.demoQuestion}>Quais pontos merecem atenção na defesa?</div>
            <div className={styles.demoAnswer}><Icon name="spark" size={19} /><div><p>Comece pela documentação contratual e pela relação entre os fatos narrados e os prejuízos alegados. Confira as provas antes de definir a estratégia. <span>[1]</span></p><div className={styles.demoCitation}><Icon name="document" size={15} /> [1] petição_inicial.pdf · trecho de exemplo</div></div></div>
            <p className={styles.demoFootnote}>Fontes disponíveis para conferência. Exemplo fictício, sem consulta à IA nesta demonstração.</p>
          </div>
          <div hidden={active !== 2} role="tabpanel" id="demo-panel-2" aria-labelledby="demo-tab-2" tabIndex={0} className={styles.demoPanel}>
            <span className={styles.demoEyebrow}>O PADRÃO DO SEU ESCRITÓRIO</span>
            <h3>Da análise à sua minuta.</h3>
            <p>Reúna os dados analisados em um documento editável.</p>
            <div className={styles.demoDocument}><span className={styles.wordIcon}>W</span><div><strong>Minuta de defesa</strong><span>Modelo do escritório · .docx</span></div><Icon name="check" size={21} /></div>
            <div className={styles.demoChecklist}>{['Selecione um template compatível', 'Gere o documento com os dados da análise', 'Revise e finalize no Word'].map((text) => <p key={text}><Icon name="check" size={16} />{text}</p>)}</div>
            <div className={styles.demoBottom}><Icon name="layers" size={16} /> Histórico de versões para acompanhar suas gerações.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
