import { Routes, Route } from "react-router";
import BrokenURL from "./pages/BrokenURL";
import TerminalPage from "./pages/TerminalPage";

const App = () => {
  return (
    <Routes>
      <Route path="/*" element={<BrokenURL />} />
      <Route path="/terminal" element={<TerminalPage />} />
    </Routes>
  );
};

export default App;
