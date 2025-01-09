// src/App.tsx
import { DiscordSummary } from "./components/DiscordSummary";

function App() {
  return (
    <div className="container mx-auto py-8">
      <div className="w-1/2">
        <img src="/tt_logo_color.svg" alt="Tenstorrent" className="" />
      </div>
      <h1 className="text-3xl font-bold mb-8">Discord Summaries</h1>
      <DiscordSummary />
    </div>
  );
}

export default App;
