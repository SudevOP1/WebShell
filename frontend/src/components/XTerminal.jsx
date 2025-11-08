import { Terminal } from "@xterm/xterm";
import { useEffect, useRef, useState } from "react";
import "@xterm/xterm/css/xterm.css";

const terminal = new Terminal();
const ws = new WebSocket("ws://localhost:8000/ws");

const XTerminal = () => {
  const terminalRef = useRef(null);
  const debug = true;
  let currentCmd = "";
  let enterPressedOnCmd = "";
  let firstResponseReceived = false;

  const debugLog = (...args) => {
    if (debug) {
      console.log(...args);
    }
  };

  // data received from backend
  useEffect(() => {
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      debugLog("receive data:", data);

      // first response from backend received, now we can using terminal
      if (!firstResponseReceived) {
        firstResponseReceived = true;
      }

      // received output of cmd
      if (data.type === "output") {
        let output = data.output;

        // remove already typed cmd from output
        if (output.startsWith(enterPressedOnCmd)) {
          output = output.replace(enterPressedOnCmd + "\r\n", "");
        }

        terminal.write(output);
        enterPressedOnCmd = "";
        currentCmd = "";
        debugLog("currentCmd:", currentCmd);
        debugLog("enterPressedOnCmd:", enterPressedOnCmd);
      }
    };
  }, []);

  useEffect(() => {
    if (!terminalRef.current) {
      return;
    }
    terminal.open(terminalRef.current);

    // key pressed
    terminal.onKey((e) => {
      if (!firstResponseReceived || enterPressedOnCmd.length !== 0) {
        return;
      }
      const key = e.key;
      const domEvent = e.domEvent;
      debugLog("key:", key);
      debugLog("domEvent.key:", domEvent.key);
      debugLog("keyCode:", domEvent.keyCode);

      // pressed enter key
      if (domEvent.keyCode === 13) {
        ws.send(
          JSON.stringify({
            type: "cmd",
            cmd: currentCmd.trim(),
          })
        );
        terminal.write("\r\n"); // in terminal, \r\n = newline (for windows)
        enterPressedOnCmd = currentCmd;
      }

      // pressed backspace key
      else if (domEvent.keyCode === 8) {
        if (currentCmd.length > 0) {
          currentCmd = currentCmd.slice(0, -1);
          terminal.write("\b \b"); // in terminal, \b \b = backspace
        }
      }

      // pressed regular character
      else {
        currentCmd += key;
        terminal.write(key);
      }

      debugLog("currentCmd", currentCmd);
      debugLog("enterPressedOnCmd:", enterPressedOnCmd);
    });

    return () => {
      terminal.dispose();
    };
  }, [terminalRef, ws]);

  return <div ref={terminalRef} className="flex-1 w-full h-full"></div>;
};

export default XTerminal;
