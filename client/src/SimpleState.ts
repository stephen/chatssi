import { EventEmitter } from "events";
import { useSyncExternalStore } from "react";

export class State<T> extends EventEmitter {
  constructor(public value: T) {
    super();
    super.setMaxListeners(200);
  }

  set(value: T) {
    this.value = value;
    this.emit("change");
  }
}

export function useSimpleState<T>(signal: State<T>): [T, (value: T) => void] {
  return [
    useSyncExternalStore(
      (listener) => {
        signal.on("change", listener);
        return () => signal.off("change", listener);
      },
      () => signal.value
    ),
    signal.set.bind(signal),
  ];
}

export function signal<T>(defaultValue: T): State<T> {
  return new State(defaultValue);
}
