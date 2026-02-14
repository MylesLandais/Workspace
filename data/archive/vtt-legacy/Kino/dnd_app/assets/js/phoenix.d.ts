// Type definitions for Phoenix libraries
// These are minimal type definitions for Phoenix, Phoenix HTML, and Phoenix LiveView

declare module "phoenix" {
  export class Socket {
    constructor(endPoint: string, opts?: SocketOptions);
    connect(): void;
    disconnect(callback?: () => void, code?: number, reason?: string): void;
    channel(topic: string, chanParams?: object): Channel;
    onOpen(callback: () => void): void;
    onClose(callback: () => void): void;
    onError(callback: (error: Error) => void): void;
    connectionState(): string;
    isConnected(): boolean;
  }

  export interface SocketOptions {
    params?: object | (() => object);
    timeout?: number;
    heartbeatIntervalMs?: number;
    reconnectAfterMs?: number | ((tries: number) => number);
    logger?: (kind: string, msg: string, data: any) => void;
    longpollerTimeout?: number;
    encode?: (payload: any, callback: (encoded: any) => void) => void;
    decode?: (payload: string, callback: (decoded: any) => void) => void;
    transport?: string;
    vsn?: string;
  }

  export class Channel {
    constructor(topic: string, params?: object, socket: Socket);
    join(timeout?: number): Push;
    leave(timeout?: number): Push;
    on(event: string, callback: (payload: any) => void): void;
    off(event: string, callback?: (payload: any) => void): void;
    push(event: string, payload: any, timeout?: number): Push;
  }

  export class Push {
    receive(status: string, callback: (payload: any) => any): Push;
  }

  export class Presence {
    static syncState(currentState: any, newState: any, onJoin?: (key: string, current: any, newPres: any) => any, onLeave?: (key: string, current: any, leftPres: any) => any): any;
    static syncDiff(currentState: any, diff: any, onJoin?: (key: string, current: any, newPres: any) => any, onLeave?: (key: string, current: any, leftPres: any) => any): any;
    static list(presences: any, chooser?: (key: string, pres: any) => any): any[];
  }
}

declare module "phoenix_html" {
  // Phoenix HTML is mostly used for CSRF tokens and form helpers
  // Minimal type definitions
  export function formData(form: HTMLFormElement): FormData;
}

declare module "phoenix_live_view" {
  export class LiveSocket {
    constructor(endPoint: string, Socket: any, opts?: LiveSocketOptions);
    connect(): void;
    disconnect(callback?: () => void): void;
    enableDebug(): void;
    enableLatencySim(ms: number): void;
    disableLatencySim(): void;
    execJS(element: Element, js: string): void;
  }

  export interface LiveSocketOptions {
    params?: object | (() => object);
    metadata?: object | ((element: Element, info: any) => object);
    dom?: DOMOptions;
  }

  export interface DOMOptions {
    onBeforeElUpdated?: (fromEl: Element, toEl: Element) => void;
    onElUpdated?: (el: Element) => void;
    skip?: (fromEl: Element, toEl: Element) => boolean;
  }
}

