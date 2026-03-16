import {env} from '@/shared/config';
import type {GameRound} from '@/shared/api';

export type WSStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error';

export type ErrorMessage = {
    type: 'error';
    message: string;
};

export type PongMessage = {
    type: 'pong';
    timestamp: string;
};

export type RoundNotificationMessage = {
    type: string; // 'round_notification' и другие типы уведомлений
    round: GameRound;
    timestamp: string;
};

export type ServerMessage = RoundNotificationMessage | ErrorMessage | PongMessage;

// Simple pub-sub using EventTarget for lightweight broadcast to many subscribers
const emitter = new EventTarget();

const STATUS_EVENT = 'status';
const MESSAGE_EVENT = 'message';

function toWsUrl(httpBase: string): string {
    try {
        // Normalize base
        const url = new URL(httpBase);
        // Convert protocol
        url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';

        // Remove trailing '/api/v1' if present (keeps compatibility with current env defaults)
        const cleanedPath = url.pathname.replace(/\/?api\/v1\/?$/, '/');
        url.pathname = cleanedPath.endsWith('/') ? cleanedPath : cleanedPath + '/';

        // Append the websocket path (ensure single slashes)
        url.pathname = (url.pathname + 'ws/betting/rounds/').replace(/\/+/g, '/');

        return url.toString();
    } catch {
        // Fallback: naive transform
        const base = httpBase.replace(/\/?api\/v1\/?$/, '/');
        const scheme = base.startsWith('https') ? 'wss' : 'ws';
        return base.replace(/^https?/, scheme).replace(/\/?$/, '/') + 'ws/betting/rounds/';
    }
}

class BettingRoundsWSClient {
    private socket: WebSocket | null = null;
    private reconnectAttempts = 0;
    private reconnectTimer: number | null = null;
    private url: string = toWsUrl(env.API_BASE_URL);
    private status: WSStatus = 'idle';

    getStatus(): WSStatus {
        return this.status;
    }

    private setStatus(next: WSStatus) {
        this.status = next;
        emitter.dispatchEvent(new CustomEvent<WSStatus>(STATUS_EVENT, {detail: next}));
    }

    connect() {
        if (
            this.socket &&
            (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)
        ) {
            return; // already connected or in progress
        }

        this.setStatus('connecting');

        try {
            this.socket = new WebSocket(this.url);
        } catch (e) {
            console.error('WebSocket init error', e);
            this.setStatus('error');
            this.scheduleReconnect();
            return;
        }

        this.socket.onopen = () => {
            this.reconnectAttempts = 0;
            this.setStatus('open');
        };

        this.socket.onmessage = (ev) => {
            let payload: ServerMessage;
            try {
                payload = JSON.parse(ev.data as string);
            } catch {
                // non-JSON payloads pass through as raw strings
                payload = ev.data;
            }
            console.log(' Received message:', payload);
            if ('round' in payload) {
                emitter.dispatchEvent(new CustomEvent<GameRound>(MESSAGE_EVENT, {detail: payload.round}));
            }
        };

        this.socket.onerror = (ev) => {
            console.error('WebSocket error', ev);
            this.setStatus('error');
        };

        this.socket.onclose = () => {
            this.setStatus('closed');
            this.scheduleReconnect();
        };
    }

    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.socket) {
            try {
                this.socket.close();
            } catch {
                /* empty */
            }
            this.socket = null;
        }
        this.setStatus('closed');
    }

    send(data: unknown) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(typeof data === 'string' ? data : JSON.stringify(data));
        } else {
            console.warn('WebSocket is not open. Cannot send message.');
        }
    }

    private scheduleReconnect() {
        // Simple exponential backoff up to 10s
        if (this.reconnectTimer) return;
        const delay = Math.min(10000, 500 * Math.pow(2, this.reconnectAttempts++));
        this.reconnectTimer = window.setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, delay);
    }
}

export const bettingRoundsWS = new BettingRoundsWSClient();

export function onStatus(listener: (status: WSStatus) => void): () => void {
    const handler = (e: Event) => listener((e as CustomEvent<WSStatus>).detail);
    emitter.addEventListener(STATUS_EVENT, handler as EventListener);
    // Emit current status immediately for new subscribers
    queueMicrotask(() => listener(bettingRoundsWS.getStatus()));
    return () => emitter.removeEventListener(STATUS_EVENT, handler as EventListener);
}

export function onMessage(listener: (msg: GameRound) => void): () => void {
    const handler = (e: Event) => listener((e as CustomEvent<GameRound>).detail);
    emitter.addEventListener(MESSAGE_EVENT, handler as EventListener);
    return () => emitter.removeEventListener(MESSAGE_EVENT, handler as EventListener);
}
