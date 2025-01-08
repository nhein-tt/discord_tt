// src/App.tsx
import { DiscordSummary } from "./components/DiscordSummary";

function App() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Discord Channel Summaries</h1>
      <DiscordSummary />
    </div>
  );
}

export default App;