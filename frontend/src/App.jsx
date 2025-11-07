import { Routes, Route } from "react-router";
import BrokenURL from "./pages/BrokenURL";
import Terminal from "./pages/Terminal";

const App = () => {
  return (
    <Routes>
      <Route path="/*" element={<BrokenURL />} />
      <Route path="/terminal" element={<Terminal />} />
    </Routes>
  );
};

export default App;
