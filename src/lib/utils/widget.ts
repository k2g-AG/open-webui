export interface WidgetMessage {
	type: string;
	data?: any;
	origin: 'open-webui-widget';
}

export interface WidgetCommand {
	type: 'open' | 'close' | 'focus' | 'newConversation' | 'setModel';
	data?: any;
}

export class WidgetBridge {
	private messageHandlers: Map<string, Function[]> = new Map();

	constructor() {
		window.addEventListener('message', this.handleMessage.bind(this));
	}

	private handleMessage(event: MessageEvent) {
		if (event.data?.origin !== 'open-webui-widget') {
			return;
		}

		const handlers = this.messageHandlers.get(event.data.type);
		if (handlers) {
			handlers.forEach(handler => handler(event.data.data));
		}
	}

	on(type: string, handler: Function) {
		if (!this.messageHandlers.has(type)) {
			this.messageHandlers.set(type, []);
		}
		this.messageHandlers.get(type)!.push(handler);
	}

	send(type: string, data?: any) {
		if (window.parent !== window) {
			window.parent.postMessage({
				type,
				data,
				origin: 'open-webui-widget'
			}, '*');
		}
	}

	// Widget-specific methods
	open() {
		this.send('open');
	}

	close() {
		this.send('close');
	}

	focus() {
		this.send('focus');
	}

	newConversation() {
		this.send('newConversation');
	}

	setModel(modelId: string) {
		this.send('setModel', { modelId });
	}
}

export const widgetBridge = new WidgetBridge();
