export default function Footer() {
  return (
    <footer className="mt-auto border-t border-linha bg-papel-alta">
      <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-2 text-[11px] text-tinta-muda sm:flex-row">
          <p>
            &copy; {new Date().getFullYear()} SmartLawer. Todos os direitos reservados.
          </p>
          <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-latiim-texto">
            IA como apoio. Revisão profissional sempre.
          </p>
        </div>
      </div>
    </footer>
  );
}
