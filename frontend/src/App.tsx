const companies = ["Google", "Amazon", "Microsoft", "NVIDIA", "Apple"];

function App() {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 px-6 py-8 font-sans text-slate-900">
      <section
        className="w-full max-w-[680px] rounded-2xl border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgb(26_39_58_/_7%)] sm:p-12 md:p-[4.5rem]"
        aria-labelledby="welcome-title"
      >
        <span className="text-xs font-bold tracking-[0.14em] text-indigo-600">
          DOCUMENT COPILOT
        </span>
        <h1
          id="welcome-title"
          className="my-4 max-w-[12ch] text-4xl leading-tight font-semibold tracking-tight sm:text-5xl"
        >
          Company filings, ready to explore.
        </h1>
        <p className="max-w-[50ch] text-base leading-relaxed text-slate-600">
          Your workspace for understanding SEC filings. Choose a company to get
          started.
        </p>
        <ul
          className="mt-8 flex flex-wrap gap-2.5"
          aria-label="Supported companies"
        >
          {companies.map((company) => (
            <li
              className="rounded-full border border-slate-200 px-3 py-2 text-sm text-slate-700"
              key={company}
            >
              {company}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

export default App;
