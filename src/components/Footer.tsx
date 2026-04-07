export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row justify-between items-center text-sm text-gray-500">
          <p>&copy; {new Date().getFullYear()} SmartLawer. All rights reserved.</p>
          <div className="flex space-x-4 mt-2 sm:mt-0">
            <a href="/privacy" className="hover:text-gray-700 transition-colors">Privacy</a>
            <a href="/terms" className="hover:text-gray-700 transition-colors">Terms</a>
            <a href="/support" className="hover:text-gray-700 transition-colors">Support</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
