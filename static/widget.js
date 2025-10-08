/**
 * Open WebUI Widget
 * Embeddable chat widget that can be integrated into any web application
 */
class OpenWebUIWidget {
  constructor(config = {}) {
    this.config = {
      src: config.src || 'http://localhost:5173/widget',
      token: config.token || '',
      theme: config.theme || 'system',
      title: config.title || 'Talk to Data',
      // Data to pass to widget
      fileId: config.fileId || '',
      fileName: config.fileName || '',
      context: config.context || '',
      metadata: config.metadata || {},
      // UI Options
      showLauncher: config.showLauncher !== false,
      autoOpen: config.autoOpen || false,
      // Positioning
      position: config.position || 'modal', // 'modal' (center) | 'dock'
      dockPosition: config.dockPosition || 'bottom-right', // when position === 'dock'
      useOverlay: config.useOverlay !== false, // show dark overlay for modal; ignored for dock
      // Sizing (can be overridden later)
      width: config.width,
      height: config.height,
      maxWidth: config.maxWidth,
      maxHeight: config.maxHeight,
      // Offsets for dock mode
      offsetX: config.offsetX ?? 24,
      offsetY: config.offsetY ?? 24,
      ...config
    };

    this.iframe = null;
    this.overlay = null;
    this.launcher = null;
    this.closeBtn = null;
    this.isOpen = false;
    this.isReady = false;
    this.messageHandlers = new Map();

    this.createElements();
    this.init();

    if (this.config.autoOpen) {
      setTimeout(() => this.open(), 500);
    }
  }

  createElements() {
    // Create overlay (may be unused for dock)
    this.overlay = document.createElement('div');
    this.overlay.className = 'open-webui-modal-overlay';
    this.overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 9998;
      display: none;
      animation: fadeIn 0.2s ease;
      background: rgba(0,0,0,0.5);
    `;

    // Create iframe
    this.iframe = document.createElement('iframe');
    this.iframe.className = 'open-webui-widget';
    const isDock = this.config.position === 'dock';
    const defaultModalWidth = this.config.width || '80%';
    const defaultModalHeight = this.config.height || '80%';
    const defaultDockWidth = this.config.width || '380px';
    const defaultDockHeight = this.config.height || '560px';

    this.iframe.style.cssText = `
      position: fixed;
      ${isDock ? '' : 'top: 50%;'}
      ${isDock ? '' : 'left: 50%;'}
      ${isDock ? '' : 'transform: translate(-50%, -50%);'}
      width: ${isDock ? defaultDockWidth : defaultModalWidth};
      max-width: ${this.config.maxWidth || (isDock ? defaultDockWidth : '1200px')};
      height: ${isDock ? defaultDockHeight : defaultModalHeight};
      max-height: ${this.config.maxHeight || (isDock ? defaultDockHeight : '800px')};
      border: none;
      border-radius: 16px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
      z-index: 10001;
      display: none;
      ${isDock ? '' : 'animation: slideUp 0.3s ease;'}
    `;

    // Create launcher button (optional)
    if (this.config.showLauncher) {
      this.launcher = document.createElement('button');
      this.launcher.className = 'open-webui-launcher';
      this.launcher.innerHTML = '💬';
      this.launcher.title = this.config.title;
      this.launcher.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 64px;
        height: 64px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 50%;
        color: white;
        font-size: 28px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
      `;
    }

    // Add animations CSS
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideUp {
        from {
          opacity: 0;
          transform: translate(-50%, -45%);
        }
        to {
          opacity: 1;
          transform: translate(-50%, -50%);
        }
      }
      .open-webui-launcher:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
      }
      .open-webui-launcher:active {
        transform: scale(0.95);
      }
    `;
    document.head.appendChild(style);

    // Append to body
    // Append to body
    document.body.appendChild(this.overlay);
    document.body.appendChild(this.iframe);
    if (this.launcher) {
      document.body.appendChild(this.launcher);
    }

    // Apply dock positioning if needed
    if (isDock) {
      this.applyDockPosition();
    }

    // Create close button (global, outside iframe)
    this.closeBtn = document.createElement('button');
    this.closeBtn.className = 'open-webui-widget-close';
    this.closeBtn.setAttribute('aria-label', 'Close chat');
    this.closeBtn.innerHTML = '&#10005;';
    this.closeBtn.style.cssText = `
      position: fixed;
      width: 28px;
      height: 28px;
      border-radius: 9999px;
      border: none;
      background: rgba(17, 24, 39, 0.8);
      color: #fff;
      font-size: 14px;
      line-height: 28px;
      text-align: center;
      cursor: pointer;
      z-index: 10002;
      display: none;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    `;
    document.body.appendChild(this.closeBtn);
    this.closeBtn.addEventListener('click', () => this.close());
  }

  init() {
    // Set iframe source with parameters
    const params = new URLSearchParams({
      theme: this.config.theme,
      title: this.config.title,
      position: this.config.position === 'dock' ? 'dock' : 'fullscreen'
    });

    if (this.config.token) params.set('token', this.config.token);
    if (this.config.fileId) params.set('fileId', this.config.fileId);
    if (this.config.fileName) params.set('fileName', this.config.fileName);
    if (this.config.context) params.set('context', this.config.context);

    this.iframe.src = `${this.config.src}?${params.toString()}`;

    // Add event listeners
    if (this.launcher) {
      this.launcher.addEventListener('click', () => this.toggle());
    }
    this.overlay.addEventListener('click', () => this.close());
    window.addEventListener('message', (e) => this.handleMessage(e));
    
    // Handle ESC key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });

    // Keep close button aligned with iframe
    window.addEventListener('resize', () => this.updateCloseBtnPosition());
    window.addEventListener('scroll', () => this.updateCloseBtnPosition(), { passive: true });
  }

  handleMessage(event) {
    if (event.data?.origin !== 'open-webui-widget') return;

    const { type, data } = event.data;

    // Trigger custom event handlers
    if (this.messageHandlers.has(type)) {
      this.messageHandlers.get(type).forEach(handler => handler(data));
    }

    // Built-in handlers
    switch (type) {
      case 'open-webui-widget-ready':
        console.log('✅ Open WebUI Widget ready');
        this.isReady = true;
        // Send initial data to widget
        this.sendData({
          fileId: this.config.fileId,
          fileName: this.config.fileName,
          context: this.config.context,
          metadata: this.config.metadata
        });
        this.emit('ready', data);
        break;
      
      case 'widget-close-request':
        this.close();
        break;

      case 'widget-closed':
        this.emit('closed');
        break;

      case 'message-sent':
        this.emit('message', data);
        break;
    }
  }

  // Event emitter pattern
  on(eventType, handler) {
    if (!this.messageHandlers.has(eventType)) {
      this.messageHandlers.set(eventType, []);
    }
    this.messageHandlers.get(eventType).push(handler);
    return this;
  }

  off(eventType, handler) {
    if (this.messageHandlers.has(eventType)) {
      const handlers = this.messageHandlers.get(eventType);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
    return this;
  }

  emit(eventType, data) {
    if (this.messageHandlers.has(eventType)) {
      this.messageHandlers.get(eventType).forEach(handler => handler(data));
    }
  }

  // Public API
  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  open() {
    this.isOpen = true;
    this.iframe.style.display = 'block';

    // Only show overlay for centered modal when enabled
    const isDock = this.config.position === 'dock';
    if (!isDock && this.config.useOverlay) {
      this.overlay.style.display = 'block';
    } else {
      this.overlay.style.display = 'none';
    }
    if (this.launcher) {
      // Keep launcher visible in dock mode (acts as anchor)
      this.launcher.style.display = isDock ? 'flex' : 'none';
    }
    // Do not lock scroll for dock mode
    document.body.style.overflow = (!isDock && this.config.useOverlay) ? 'hidden' : '';
    // Show and place close button
    this.updateCloseBtnPosition();
    this.closeBtn.style.display = 'block';
    this.emit('open');
  }

  close() {
    this.isOpen = false;
    this.iframe.style.display = 'none';
    this.overlay.style.display = 'none';
    if (this.launcher) {
      this.launcher.style.display = 'flex';
    }
    document.body.style.overflow = '';
    if (this.closeBtn) {
      this.closeBtn.style.display = 'none';
    }
    
    // Notify widget about close
    if (this.isReady) {
      this.sendMessage('widget-close');
    }
    this.emit('close');
  }

  // Update widget data dynamically
  sendData(data) {
    this.sendMessage('widget-set-data', data);
  }

  sendMessage(type, data) {
    if (this.iframe?.contentWindow) {
      this.iframe.contentWindow.postMessage({
        type,
        data,
        origin: 'parent-app'
      }, '*');
    }
  }

  // Public methods for external control
  updateFileId(fileId, fileName = '') {
    this.config.fileId = fileId;
    this.config.fileName = fileName;
    this.sendData({ fileId, fileName });
  }

  setContext(context) {
    this.config.context = context;
    this.sendData({ context });
  }

  setMetadata(metadata) {
    this.config.metadata = { ...this.config.metadata, ...metadata };
    this.sendData({ metadata: this.config.metadata });
  }

  destroy() {
    this.overlay?.remove();
    this.iframe?.remove();
    this.launcher?.remove();
    this.messageHandlers.clear();
  }

  // Helpers
  applyDockPosition() {
    const pos = this.config.dockPosition || 'bottom-right';
    const offsetX = `${this.config.offsetX ?? 24}px`;
    const offsetY = `${this.config.offsetY ?? 24}px`;

    this.iframe.style.top = 'auto';
    this.iframe.style.left = 'auto';
    this.iframe.style.transform = 'none';

    if (pos.includes('bottom')) {
      this.iframe.style.bottom = offsetY;
      this.iframe.style.top = 'auto';
    } else {
      this.iframe.style.top = offsetY;
      this.iframe.style.bottom = 'auto';
    }

    if (pos.includes('right')) {
      this.iframe.style.right = offsetX;
      this.iframe.style.left = 'auto';
    } else {
      this.iframe.style.left = offsetX;
      this.iframe.style.right = 'auto';
    }

    // Ensure it's above launcher
    this.iframe.style.zIndex = '10001';
    this.updateCloseBtnPosition();
  }

  updateCloseBtnPosition() {
    if (!this.closeBtn || this.iframe.style.display === 'none') return;
    const rect = this.iframe.getBoundingClientRect();
    // Place close button slightly outside top-right corner of the iframe
    const gap = 8; // px
    const size = 28; // button size
    const top = Math.max(8, rect.top - (size / 2) + gap);
    const left = rect.right - (size / 2) - gap;
    this.closeBtn.style.top = `${top}px`;
    this.closeBtn.style.left = `${left}px`;
  }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OpenWebUIWidget;
}
if (typeof window !== 'undefined') {
  window.OpenWebUIWidget = OpenWebUIWidget;
}

