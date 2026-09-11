export default function Footer() {
  return (
    <footer className="mt-auto border-t border-ouro-700/20 bg-tribunal-950">
      <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-2 text-sm text-zinc-500 sm:flex-row">
          <p>
            &copy; {new Date().getFullYear()} SmartLawer. Excelência jurídica para a advocacia brasileira.
          </p>
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-ouro-600">
            Feito para o mercado brasileiro
          </p>
        </div>
      </div>
    </footer>
  );
}
