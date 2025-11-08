import { Terminal } from "@xterm/xterm";
import { useEffect, useRef, useState } from "react";
import "@xterm/xterm/css/xterm.css";

const terminal = new Terminal();
const ws = new WebSocket("ws://localhost:8000/ws");

const XTerminal = () => {
  const terminalRef = useRef(null);
  let currentCmd = "";
  let enterPressedOnCmd = "";

  useEffect(() => {
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "output") {
        let output = data.output;
        if (output.startsWith(enterPressedOnCmd)) {
          output = output.replace(enterPressedOnCmd + "\r\n", "");
        }
        terminal.write(output);
        enterPressedOnCmd = "";
        currentCmd = "";
      }
    };
  }, []);

  useEffect(() => {
    if (!terminalRef.current) {
      return;
    }
    terminal.open(terminalRef.current);
    terminal.onKey((e) => {
      if (enterPressedOnCmd.length === 0) {
        const key = e.key;
        const domEvent = e.domEvent;
        console.log(
          "key:",
          key,
          "domEvent.key:",
          domEvent.key,
          "keyCode:",
          domEvent.keyCode
        );

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

        console.log("currentCmd", currentCmd);
      }
    });
    return () => {
      terminal.dispose();
    };
  }, [terminalRef, ws]);

  return <div ref={terminalRef} className="flex-1 w-full h-full"></div>;
};

export default XTerminal;
