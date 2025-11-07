import { Terminal } from "@xterm/xterm";
import { useEffect, useRef } from "react";
import "@xterm/xterm/css/xterm.css";

const terminal = new Terminal();

const XTerminal = () => {
  const terminalRef = useRef(null);

  useEffect(() => {
    if (!terminalRef.current) {
      return;
    }
    terminal.open(terminalRef.current);
    terminal.write("Hello from \x1B[1;3;31mxterm.js\x1B[0m $ ");
  }, [terminalRef]);

  return <div ref={terminalRef} className="flex-1 w-full h-full"></div>;
};

export default XTerminal;
