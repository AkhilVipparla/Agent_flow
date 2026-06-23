export function SettingsPage() {
  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="space-y-4">
        {[
          { title: 'Organisation', description: 'Manage organisation name, logo, and billing details.' },
          { title: 'API Keys', description: 'Configure LLM provider keys and integration credentials.' },
          { title: 'Notifications', description: 'Set up email or webhook alerts for completed research runs.' },
        ].map(({ title, description }) => (
          <div key={title} className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-1">{title}</h2>
            <p className="text-sm text-gray-500">{description}</p>
            <button className="mt-3 px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors">
              Configure
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
