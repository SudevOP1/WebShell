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

  useEffect(() => {
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      debugLog("receive data:", data);

      if (!firstResponseReceived) {
        firstResponseReceived = true;
      }
      if (data.type === "output") {
        let output = data.output;

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
    terminal.onKey((e) => {
      if (firstResponseReceived && enterPressedOnCmd.length === 0) {
        const key = e.key;
        const domEvent = e.domEvent;
        debugLog("key:", key);
        debugLog("domEvent.key:", domEvent.key);
        debugLog("keyCode:", domEvent.keyCode);

        // enter key pressed
        if (domEvent.keyCode === 13) {
          ws.send(
            JSON.stringify({
              type: "cmd",
              cmd: currentCmd.trim(),
            })
          );
          terminal.write("\r\n");
          enterPressedOnCmd = currentCmd;
        }

        // backspace key pressed
        else if (domEvent.keyCode === 8) {
          if (currentCmd.length > 0) {
            currentCmd = currentCmd.slice(0, -1);
            terminal.write("\b \b");
          }
        }

        // regular character pressed
        else {
          currentCmd += key;
          terminal.write(key);
        }

        debugLog("currentCmd", currentCmd);
        debugLog("enterPressedOnCmd:", enterPressedOnCmd);
      }
    });
    return () => {
      terminal.dispose();
    };
  }, [terminalRef, ws]);

  return <div ref={terminalRef} className="flex-1 w-full h-full"></div>;
};

export default XTerminal;
