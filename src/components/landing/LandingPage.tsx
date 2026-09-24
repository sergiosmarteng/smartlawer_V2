import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';
import { useAuth } from '../auth/AuthProvider';
import Icon, { type IconName } from './Icon';
import ProductDemo from './ProductDemo';
import styles from './landing.module.css';

const features: Array<{ icon: IconName; title: string; description: string; tag: string }> = [
  { icon: 'document', title: 'Encontre o essencial da petição.', description: 'Fatos, pedidos, fundamentos citados, provas e sugestões de teses defensivas em uma análise estruturada para sua revisão.', tag: 'ANÁLISE JURÍDICA' },
  { icon: 'chat', title: 'Pergunte. Aprofunde. Confira.', description: 'Converse sobre um caso, explore os documentos e consulte os trechos apresentados como fonte para conferir as respostas.', tag: 'CHAT COM DOCUMENTOS' },
  { icon: 'download', title: 'Sua minuta, no seu padrão.', description: 'Use um modelo DOCX compatível do escritório e gere uma base editável com os dados da análise. Ajuste a redação e dê o seu acabamento.', tag: 'DOCUMENTOS EM WORD' },
  { icon: 'layers', title: 'Mais continuidade entre os casos.', description: 'Envie até 10 PDFs por lote, acompanhe o processamento e consulte análises e versões geradas em um único ambiente.', tag: 'ORGANIZAÇÃO DO TRABALHO' },
];

const steps = [
  { icon: 'upload' as const, number: '01', title: 'Envie a petição.', description: 'Carregue o PDF de um caso ou envie um lote de documentos. Acompanhe o processamento pelo painel.' },
  { icon: 'spark' as const, number: '02', title: 'Enxergue os pontos-chave.', description: 'Leia a análise estruturada, confira os pedidos e aprofunde as questões no chat com os documentos.' },
  { icon: 'download' as const, number: '03', title: 'Construa sua defesa.', description: 'Escolha um template, gere o DOCX e finalize a minuta com sua experiência e revisão profissional.' },
];

const questions = [
  { question: 'O que é o SmartLawer?', answer: 'É uma plataforma de inteligência artificial para apoiar o trabalho de advogados com petições e documentos. Ela reúne análise de PDFs, chat com consulta aos documentos, geração de minutas em DOCX, templates e histórico em um mesmo fluxo de trabalho.' },
  { question: 'Como ele pode melhorar minha produtividade?', answer: 'O SmartLawer ajuda a reduzir o trabalho de organizar informações da petição e preparar a base de uma minuta. Assim, você pode dedicar mais atenção à conferência das provas, à definição da estratégia e ao atendimento ao cliente. O ganho depende da complexidade do caso, da qualidade do documento e da revisão necessária.' },
  { question: 'Preciso saber usar inteligência artificial?', answer: 'Não é necessário programar ou configurar modelos para iniciar o fluxo básico. Crie sua conta, envie uma petição em PDF, acompanhe a análise e faça perguntas em linguagem natural. Se desejar, use perfis de orientação para personalizar as análises do seu escritório.' },
  { question: 'Posso usar os modelos de documentos do meu escritório?', answer: 'Sim. É possível enviar um template em DOCX com os campos compatíveis com a análise, selecioná-lo e gerar uma minuta editável. O sistema informa campos não suportados para que você ajuste o modelo antes de gerar o documento.' },
  { question: 'A IA substitui a análise do advogado?', answer: 'Não. As análises, respostas e minutas são rascunhos de apoio. Confira os fatos, os trechos citados, a legislação aplicável e a adequação das teses ao caso. A decisão, a revisão e o uso profissional continuam sob responsabilidade do advogado. O sistema não protocola peças automaticamente.' },
  { question: 'O chat pesquisa toda a jurisprudência dos tribunais?', answer: 'Não. O chat trabalha com os documentos disponíveis no sistema e, quando aplicável, com uma base selecionada de referências. Ele não oferece cobertura completa ou atualização em tempo real dos tribunais. Confira sempre a origem, a vigência e a pertinência de cada fundamento.' },
];

function Brand({ light = false }: { light?: boolean }) {
  return <Link href="/" className={`${styles.brand} ${light ? styles.brandLight : ''}`} aria-label="SmartLawer — início"><span className={styles.brandMark}><Icon name="scale" size={25} /></span><span>Smart<span className={styles.brandAccent}>Lawer</span><small>INTELIGÊNCIA JURÍDICA</small></span></Link>;
}

export default function LandingPage() {
  const { user } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const ctaHref = user ? '/dashboard' : '/sign-up';
  const ctaLabel = user ? 'Abrir meu painel' : 'Começar agora';

  return (
    <div className={styles.site}>
      <a className={styles.skipLink} href="#conteudo">Pular para o conteúdo</a>
      <header className={styles.header}>
        <div className={`${styles.container} ${styles.headerInner}`}>
          <Brand />
          <nav className={styles.desktopNav} aria-label="Navegação principal"><a href="#plataforma">A plataforma</a><a href="#como-funciona">Como funciona</a><a href="#diferenciais">Por que SmartLawer</a><a href="#duvidas">Dúvidas</a></nav>
          <div className={styles.headerActions}><Link className={styles.signIn} href={user ? '/dashboard' : '/sign-in'}>{user ? 'Meu painel' : 'Entrar'}</Link><Link href={ctaHref} className={styles.headerCta}>{user ? 'Acessar' : 'Criar minha conta'}<Icon name="diagonal" size={16} /></Link><button type="button" className={styles.menuToggle} aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'} aria-expanded={menuOpen} aria-controls="landing-menu" onClick={() => setMenuOpen(!menuOpen)}><Icon name={menuOpen ? 'close' : 'menu'} /></button></div>
        </div>
        {menuOpen && <nav id="landing-menu" className={styles.mobileNav} aria-label="Navegação mobile" onKeyDown={(event) => { if (event.key === 'Escape') { setMenuOpen(false); (document.querySelector('[aria-controls="landing-menu"]') as HTMLButtonElement)?.focus(); } }}><a href="#plataforma" onClick={() => setMenuOpen(false)}>A plataforma</a><a href="#como-funciona" onClick={() => setMenuOpen(false)}>Como funciona</a><a href="#diferenciais" onClick={() => setMenuOpen(false)}>Por que SmartLawer</a><a href="#duvidas" onClick={() => setMenuOpen(false)}>Dúvidas frequentes</a><Link href={user ? '/dashboard' : '/sign-in'}>{user ? 'Meu painel' : 'Entrar na minha conta'}</Link></nav>}
      </header>

      <main id="conteudo">
        <section className={styles.hero} aria-labelledby="hero-title">
          <div className={styles.heroImage}><Image src="/images/landing/justice-architecture.png" alt="Balança de latão em equilíbrio, entre mármore verde e travertino iluminado pelo sol" fill priority sizes="(max-width: 760px) 100vw, 65vw" quality={85} /></div>
          <div className={styles.heroShade} />
          <div className={`${styles.container} ${styles.heroContent}`}>
            <div className={styles.eyebrowLight}><span /> A NOVA PERSPECTIVA DA ADVOCACIA</div>
            <h1 id="hero-title">Seu talento é<br />a estratégia.<br /><em>O trabalho pesado<br />é nosso.</em></h1>
            <p>Transforme petições em clareza. Organize os fatos, explore caminhos para a defesa e prepare minutas com inteligência artificial — e com você no comando.</p>
            <div className={styles.heroActions}><Link href={ctaHref} className={styles.buttonGold}>{ctaLabel}<Icon name="arrow" /></Link><a className={styles.heroSecondary} href="#como-funciona"><span className={styles.playIcon}>↗</span>Conhecer a plataforma</a></div>
            <div className={styles.heroNote}><Icon name="check" size={16} /> Feito para a advocacia brasileira.<span>Decisões sempre humanas.</span></div>
          </div>
          <div className={styles.heroCaption}><span className={styles.captionLine} /><span>TECNOLOGIA A SERVIÇO<br /><strong>DO SEU MELHOR ARGUMENTO.</strong></span></div>
          <div className={styles.heroNumber}>01 — UMA NOVA FORMA DE ADVOGAR</div>
        </section>

        <div className={styles.promiseStrip}><div className={styles.container}><span>DA PRIMEIRA LEITURA À SUA MINUTA.</span><p><Icon name="document" /> Análise estruturada</p><p><Icon name="chat" /> Chat com fontes</p><p><Icon name="download" /> DOCX no seu modelo</p><p><Icon name="shield" /> Você no controle</p></div></div>

        <section id="plataforma" className={`${styles.section} ${styles.platform}`} aria-labelledby="platform-title">
          <div className={styles.container}>
            <div className={styles.sectionIntro}><div><span className={styles.eyebrow}>INTELIGÊNCIA QUE TRABALHA COM VOCÊ</span><h2 id="platform-title">Menos tarefas repetitivas.<br /><em>Mais advocacia.</em></h2></div><p>Seu tempo tem valor. O SmartLawer reúne leitura assistida, pesquisa nos documentos e preparação de minutas para você se concentrar no que exige o seu olhar.</p></div>
            <div className={styles.featureGrid}>{features.map((feature) => <article key={feature.tag} className={styles.feature}><div className={styles.featureTop}><span className={styles.featureIcon}><Icon name={feature.icon} size={25} /></span><span>{feature.tag}</span></div><h3>{feature.title}</h3><p>{feature.description}</p></article>)}</div>
          </div>
        </section>

        <section id="como-funciona" className={`${styles.section} ${styles.howSection}`} aria-labelledby="how-title">
          <div className={styles.container}>
            <div className={styles.centerIntro}><span className={styles.eyebrow}>UM FLUXO SIMPLES. UMA VISÃO MAIS COMPLETA.</span><h2 id="how-title">Da petição ao próximo passo.<br /><em>Sem perder o fio do caso.</em></h2><p>Conheça o caminho que conecta informação, análise e ação.</p></div>
            <ProductDemo />
            <div className={styles.steps}>{steps.map((step) => <article key={step.number}><div className={styles.stepTop}><span>{step.number}</span><Icon name={step.icon} size={22} /></div><h3>{step.title}</h3><p>{step.description}</p></article>)}</div>
            <div className={styles.centerCta}><Link href={ctaHref} className={styles.buttonDark}>{user ? 'Continuar no meu painel' : 'Quero analisar meu primeiro caso'}<Icon name="arrow" size={18} /></Link></div>
          </div>
        </section>

        <section id="diferenciais" className={styles.performance} aria-labelledby="performance-title">
          <div className={styles.performancePhoto}><Image src="/images/landing/lawyer-strategy.png" alt="Advogada revisando documentos com atenção em um escritório iluminado por luz natural" fill sizes="(max-width: 900px) 100vw, 50vw" quality={85} /><span className={styles.photoCaption}>MAIS ESPAÇO PARA O QUE SÓ VOCÊ FAZ.</span></div>
          <div className={styles.performanceContent}><span className={styles.eyebrowLight}>PERFORMANCE COM PROPÓSITO</span><h2 id="performance-title">O diferencial<br />continua sendo você.<br /><em>Agora, com mais foco.</em></h2><p>A tecnologia cuida da organização inicial. Sua experiência transforma informação em uma estratégia que faz sentido para cada cliente.</p><div className={styles.benefit}><span>01</span><div><h3>Comece com uma visão organizada.</h3><p>Tenha os pontos da petição reunidos para orientar sua leitura e identificar o que precisa ser aprofundado.</p></div></div><div className={styles.benefit}><span>02</span><div><h3>Troque o retrabalho por continuidade.</h3><p>Leve os dados da análise para a minuta e mantenha o padrão do escritório com templates compatíveis.</p></div></div><div className={styles.benefit}><span>03</span><div><h3>Dedique atenção ao que importa.</h3><p>Use o tempo com mais intenção: revisar os fundamentos, preparar a estratégia e estar perto do cliente.</p></div></div></div>
        </section>

        <section className={`${styles.section} ${styles.trustSection}`} aria-labelledby="trust-title"><div className={styles.container}><div className={styles.trustHeading}><span className={styles.trustSeal}><Icon name="shield" size={32} /></span><span className={styles.eyebrow}>INTELIGÊNCIA ARTIFICIAL. RESPONSABILIDADE PROFISSIONAL.</span><h2 id="trust-title">Tecnologia como apoio.<br /><em>Seu critério como direção.</em></h2><p>Uma boa ferramenta amplia sua capacidade de análise e preserva o papel de quem conhece o Direito e o cliente.</p></div><div className={styles.trustGrid}><article><Icon name="document" size={25} /><h3>Fontes para conferir</h3><p>Consulte os trechos apresentados no chat e confronte as respostas com os documentos do caso.</p></article><article><Icon name="layers" size={25} /><h3>Histórico para acompanhar</h3><p>Acesse versões de documentos gerados e a trilha de eventos da sua conta para acompanhar seu trabalho.</p></article><article><Icon name="shield" size={25} /><h3>Revisão em cada entrega</h3><p>Você valida a análise, ajusta a minuta e decide o próximo passo. O SmartLawer não protocola peças por você.</p></article></div></div></section>

        <section id="duvidas" className={`${styles.section} ${styles.faqSection}`} aria-labelledby="faq-title"><div className={`${styles.container} ${styles.faqLayout}`}><div><span className={styles.eyebrow}>ANTES DO PRIMEIRO CASO</span><h2 id="faq-title">Boas perguntas.<br /><em>Respostas claras.</em></h2><p>Conheça as possibilidades e o papel do SmartLawer na rotina do seu escritório.</p><Link href={ctaHref} className={styles.textLink}>{user ? 'Ir para o meu painel' : 'Conhecer na prática'}<Icon name="diagonal" size={18} /></Link></div><div className={styles.faqList}>{questions.map((item) => <details key={item.question} className={styles.faqItem}><summary>{item.question}<span><Icon name="plus" size={19} /></span></summary><p>{item.answer}</p></details>)}</div></div></section>

        <section className={styles.finalSection} aria-labelledby="final-title"><div className={styles.finalArt} aria-hidden="true"><span /><span /><span /></div><div className={styles.container}><span className={styles.eyebrowLight}>SEU PRÓXIMO CASO MERECE UMA NOVA PERSPECTIVA</span><h2 id="final-title">Mais tempo para pensar.<br /><em>Mais espaço para ir além.</em></h2><p>Conheça uma forma mais inteligente de organizar<br className={styles.desktopBreak} /> documentos e construir sua próxima estratégia.</p><Link href={ctaHref} className={styles.buttonGold}>{user ? 'Abrir meu painel' : 'Começar com SmartLawer'}<Icon name="arrow" /></Link><span className={styles.finalNote}>Da petição à minuta. Com você no comando.</span></div></section>
      </main>

      <footer className={styles.footer}><div className={styles.container}><div className={styles.footerTop}><div><Brand light /><p>Inteligência a serviço do Direito.<br />Tecnologia a serviço de você.</p></div><nav aria-label="Navegação do rodapé"><span>EXPLORE</span><a href="#plataforma">A plataforma</a><a href="#como-funciona">Como funciona</a><a href="#diferenciais">Por que SmartLawer</a></nav><nav aria-label="Acesso ao sistema"><span>SEU PRÓXIMO PASSO</span><Link href={ctaHref}>{user ? 'Meu painel' : 'Criar minha conta'}</Link><Link href="/sign-in">Entrar no sistema</Link><a href="#duvidas">Dúvidas frequentes</a></nav><div className={styles.footerSignature}><span>FEITO PARA A</span><p>advocacia<br /><em>brasileira.</em></p></div></div><div className={styles.footerBottom}><span>© {new Date().getFullYear()} SmartLawer. Todos os direitos reservados.</span><span>IA como apoio. Revisão profissional sempre.</span></div></div></footer>
    </div>
  );
}
