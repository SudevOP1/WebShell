import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { useEffect, useRef } from "react";
import "@xterm/xterm/css/xterm.css";

const terminal = new Terminal();
const fitAddon = new FitAddon();
const ws = new WebSocket("ws://localhost:8000/ws");

const XTerminal = () => {
  const terminalRef = useRef(null);
  const debug = true;
  let currentCmd = "";
  let enterPressedOnCmd = "";
  let firstResponseReceived = false;
  let previouslyRunCmds = [];
  let previouslyRunCmdsIndex = 0;
  let currentCmdWhileTogglingPreviouslyRunCmds = "";

  const debugLog = (...args) => {
    if (debug) {
      console.log(...args);
    }
  };

  const rewriteCurrentCmd = (cmd) => {
    const numBackspaces = "\b \b".repeat(currentCmd.length);
    terminal.write(numBackspaces);
    terminal.write(cmd);
  };

  // data received from backend
  useEffect(() => {
    ws.onopen = () => debugLog("ws connected");

    ws.onclose = () => debugLog("ws disconnected");

    ws.onerror = (e) => debugLog("ws error:", e);

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

    // closing ws here
    window.addEventListener("beforeunload", () => ws.close());
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (!terminalRef.current) {
      return;
    }

    // fit addon stuff (for terminal resizing)
    terminal.loadAddon(fitAddon);
    terminal.open(terminalRef.current);
    fitAddon.fit();
    const handleResize = () => {
      fitAddon.fit();
    };
    window.addEventListener("resize", handleResize);

    // handle key pressed before xterm handles them
    terminal.attachCustomKeyEventHandler((domEvent) => {
      // block keys not in allowedKeyCodes
      if (!allowedKeyCodes.includes(domEvent.keyCode)) {
        debugLog("Blocked key:", domEvent.keyCode);
        // return false to prevent xterm from handling this key
        return false;
      }
      // return true to let xterm handle allowed keys normally
      return true;
    });

    // key pressed
    terminal.onKey((e) => {
      const key = e.key;
      const domEvent = e.domEvent;

      // handle keys pressed only when:
      // (first response from backend received)
      // and (not waiting for output of previous cmd)
      if (!firstResponseReceived || enterPressedOnCmd.length !== 0) {
        return;
      }

      debugLog("key:", key);
      debugLog("domEvent.key:", domEvent.key);
      debugLog("keyCode:", domEvent.keyCode);

      // pressed enter key
      if (domEvent.keyCode === 13) {
        if (!(ws && ws.readyState === WebSocket.OPEN)) {
          alert("websocket session expired. please refresh the page");
          return;
        }
        ws.send(
          JSON.stringify({
            type: "cmd",
            cmd: currentCmd.trim(),
          })
        );
        terminal.write("\r\n"); // \r\n = newline (for windows terminals)
        enterPressedOnCmd = currentCmd;
        previouslyRunCmds.push(currentCmd);

        // reset index to point after the last command
        previouslyRunCmdsIndex = previouslyRunCmds.length;
        currentCmdWhileTogglingPreviouslyRunCmds = "";
      }

      // pressed backspace key
      else if (domEvent.keyCode === 8) {
        if (currentCmd.length > 0) {
          currentCmd = currentCmd.slice(0, -1);
          terminal.write("\b \b"); // \b \b = backspace

          // if we're in history navigation mode, update the saved command too
          if (previouslyRunCmdsIndex !== previouslyRunCmds.length) {
            currentCmdWhileTogglingPreviouslyRunCmds = currentCmd;
          }
        }
      }

      // pressed up arrow, navigate to previous cmd in history
      else if (domEvent.keyCode === 38) {
        // save current command if we're at the bottom of history to currentCmdWhileTogglingPreviouslyRunCmds
        if (previouslyRunCmdsIndex === previouslyRunCmds.length) {
          currentCmdWhileTogglingPreviouslyRunCmds = currentCmd;
        }

        // move up in history (if not at top)
        if (previouslyRunCmdsIndex > 0) {
          previouslyRunCmdsIndex -= 1;
          const oldCmd = currentCmd;
          currentCmd = previouslyRunCmds[previouslyRunCmdsIndex];

          // clear old command before writing new one
          const numBackspaces = "\b \b".repeat(oldCmd.length);
          terminal.write(numBackspaces);
          terminal.write(currentCmd);
        }

        // if at top of history, reset to the currentCmdWhileTogglingPreviouslyRunCmds
        else if (previouslyRunCmdsIndex === 0) {
          const oldCmd = currentCmd;
          previouslyRunCmdsIndex = previouslyRunCmds.length;
          currentCmd = currentCmdWhileTogglingPreviouslyRunCmds;
          currentCmdWhileTogglingPreviouslyRunCmds = "";

          // clear old command before writing new one
          const numBackspaces = "\b \b".repeat(oldCmd.length);
          terminal.write(numBackspaces);
          terminal.write(currentCmd);
        }
      }

      // pressed down arrow, navigate to next cmd in history
      else if (domEvent.keyCode === 40) {
        if (previouslyRunCmds.length === 0) return;

        // move down in history (if not at bottom)
        if (previouslyRunCmdsIndex < previouslyRunCmds.length - 1) {
          previouslyRunCmdsIndex += 1;
          const oldCmd = currentCmd;
          currentCmd = previouslyRunCmds[previouslyRunCmdsIndex];

          // clear old command before writing new one
          const numBackspaces = "\b \b".repeat(oldCmd.length);
          terminal.write(numBackspaces);
          terminal.write(currentCmd);
        }

        // if at the last command, reset to the currentCmdWhileTogglingPreviouslyRunCmds
        else if (previouslyRunCmdsIndex === previouslyRunCmds.length - 1) {
          const oldCmd = currentCmd;
          previouslyRunCmdsIndex = previouslyRunCmds.length;
          currentCmd = currentCmdWhileTogglingPreviouslyRunCmds;
          currentCmdWhileTogglingPreviouslyRunCmds = "";

          // clear old command before writing new one
          const numBackspaces = "\b \b".repeat(oldCmd.length);
          terminal.write(numBackspaces);
          terminal.write(currentCmd);
        }
      }

      // pressed regular character
      else {
        // if we're in history navigation mode, append input char to historical cmd
        if (previouslyRunCmdsIndex !== previouslyRunCmds.length) {
          previouslyRunCmdsIndex = previouslyRunCmds.length;
          currentCmdWhileTogglingPreviouslyRunCmds = "";
        }
        currentCmd += key;
        terminal.write(key);
      }

      debugLog("currentCmd:", currentCmd);
      debugLog("enterPressedOnCmd:", enterPressedOnCmd);
      debugLog("previouslyRunCmdsIndex:", previouslyRunCmdsIndex);
      debugLog(
        "currentCmdWhileTogglingPreviouslyRunCmds:",
        currentCmdWhileTogglingPreviouslyRunCmds
      );
    });

    return () => {
      window.removeEventListener("resize", handleResize);
      terminal.dispose();
    };
  }, [terminalRef, ws]);

  return <div ref={terminalRef} className="flex-1 w-full h-full"></div>;
};

export default XTerminal;

let numberKeyCodes = [
  48, // 0
  49, // 1
  50, // 2
  51, // 3
  52, // 4
  53, // 5
  54, // 6
  55, // 7
  56, // 8
  57, // 9
];

let alphabetKeyCodes = [
  65, // A
  66, // B
  67, // C
  68, // D
  69, // E
  70, // F
  71, // G
  72, // H
  73, // I
  74, // J
  75, // K
  76, // L
  77, // M
  78, // N
  79, // O
  80, // P
  81, // Q
  82, // R
  83, // S
  84, // T
  85, // U
  86, // V
  87, // W
  88, // X
  89, // Y
  90, // Z
];

let punctuationKeyCodes = [
  186, // ;
  187, // =
  188, // ,
  189, // -
  190, // .
  191, // /
  192, // `
  219, // [
  220, // \
  221, // ]
  222, // '
];

let upDownArrowKeyCodes = [
  38, // up arrow
  40, // down arrow
];

let allowedKeyCodes = [
  8, // backspace
  13, // enter
  16, // shift
  20, // caps lock
  32, // space
  ...numberKeyCodes,
  ...alphabetKeyCodes,
  ...punctuationKeyCodes,
  ...upDownArrowKeyCodes,
];
