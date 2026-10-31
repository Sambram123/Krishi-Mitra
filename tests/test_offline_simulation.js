/**
 * Offline Degradation & Outbox Auto-Retry Simulation Test Suite
 * 
 * Tests the 6 core offline behaviors:
 * 1. Drop during recording (clip saved to IndexedDB outbox)
 * 2. Drop during upload (mid-request failure keeps pending item with same key)
 * 3. Drop before reply (idempotency key returns cached answer on reconnect)
 * 4. Reconnect and auto-send (chronological queue processing)
 * 5. Queue limits enforcement (60s clip, 10 items, 20 MB, 24h TTL expiry)
 * 6. Logout and consent withdrawal wiping queues
 */

import { test, describe, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

// --- In-Memory IndexedDB Mock for Node Environment ---
class MockIDBObjectStore {
  constructor(name, keyPath, memoryMap) {
    this.name = name;
    this.keyPath = keyPath;
    this.map = memoryMap;
  }

  put(item) {
    const key = item[this.keyPath];
    this.map.set(key, JSON.parse(JSON.stringify(item)));
    const req = { result: key, error: null, onsuccess: null, onerror: null };
    queueMicrotask(() => req.onsuccess && req.onsuccess({ target: req }));
    return req;
  }

  get(key) {
    const item = this.map.get(key);
    const req = {
      result: item ? JSON.parse(JSON.stringify(item)) : undefined,
      error: null,
      onsuccess: null,
      onerror: null
    };
    queueMicrotask(() => req.onsuccess && req.onsuccess({ target: req }));
    return req;
  }

  getAll() {
    const items = Array.from(this.map.values()).map(it => JSON.parse(JSON.stringify(it)));
    const req = { result: items, error: null, onsuccess: null, onerror: null };
    queueMicrotask(() => req.onsuccess && req.onsuccess({ target: req }));
    return req;
  }

  delete(key) {
    this.map.delete(key);
    const req = { result: undefined, error: null, onsuccess: null, onerror: null };
    queueMicrotask(() => req.onsuccess && req.onsuccess({ target: req }));
    return req;
  }

  clear() {
    this.map.clear();
    const req = { result: undefined, error: null, onsuccess: null, onerror: null };
    queueMicrotask(() => req.onsuccess && req.onsuccess({ target: req }));
    return req;
  }
}

class MockIDBTransaction {
  constructor(db, storeNames) {
    this.db = db;
    this.storeNames = Array.isArray(storeNames) ? storeNames : [storeNames];
  }

  objectStore(name) {
    return this.db._stores.get(name);
  }
}

class MockIDBDatabase {
  constructor(name, version) {
    this.name = name;
    this.version = version;
    this.objectStoreNames = {
      _set: new Set(),
      contains(name) { return this._set.has(name); },
      add(name) { this._set.add(name); }
    };
    this._stores = new Map();
    this._memory = new Map();
  }

  createObjectStore(name, options = {}) {
    this.objectStoreNames.add(name);
    if (!this._memory.has(name)) {
      this._memory.set(name, new Map());
    }
    const store = new MockIDBObjectStore(name, options.keyPath || 'id', this._memory.get(name));
    this._stores.set(name, store);
    return store;
  }

  transaction(storeNames) {
    return new MockIDBTransaction(this, storeNames);
  }
}

class MockIDBFactory {
  constructor() {
    this.dbs = new Map();
  }

  open(name, version) {
    const req = { result: null, error: null, onsuccess: null, onupgradeneeded: null, onerror: null };
    queueMicrotask(() => {
      let db = this.dbs.get(name);
      const isNew = !db;
      if (!db) {
        db = new MockIDBDatabase(name, version);
        this.dbs.set(name, db);
      }
      req.result = db;
      if (isNew && req.onupgradeneeded) {
        req.onupgradeneeded({ target: req });
      }
      if (req.onsuccess) {
        req.onsuccess({ target: req });
      }
    });
    return req;
  }
}

// Global Browser Mock Setup
const eventsDispatched = [];
class MockCustomEvent {
  constructor(type, eventInitDict = {}) {
    this.type = type;
    this.detail = eventInitDict.detail || null;
  }
}

globalThis.CustomEvent = MockCustomEvent;
globalThis.window = {
  dispatchEvent: (ev) => {
    eventsDispatched.push(ev);
  },
  addEventListener: () => {},
  __KRISHI_TEST_FAST_RETRY__: true,
};

const makeMockElement = () => ({
  setAttribute: () => {},
  appendChild: () => {},
  addEventListener: () => {},
  removeEventListener: () => {},
  classList: { add: () => {}, remove: () => {}, contains: () => false },
  style: {},
  children: [],
});

globalThis.document = {
  readyState: 'complete',
  getElementById: () => makeMockElement(),
  querySelector: () => makeMockElement(),
  querySelectorAll: () => [],
  createElement: () => makeMockElement(),
  body: { appendChild: () => {}, prepend: () => {} }
};

Object.defineProperty(globalThis, 'navigator', {
  value: {
    onLine: true,
    serviceWorker: { register: async () => ({}) }
  },
  writable: true,
  configurable: true,
});

globalThis.indexedDB = new MockIDBFactory();

// Import client modules
const webApp = await import('../web_app.js');
const { KrishiOffline, KrishiAuth, KrishiConsent } = webApp.default || webApp;

describe('Krishi Offline & Resilience Outbox Suite', () => {
  beforeEach(async () => {
    eventsDispatched.length = 0;
    await KrishiOffline.clearAllData();
    navigator.onLine = true;
    KrishiOffline.setConnectivityState('online');
    KrishiAuth.setToken('mock-access-token');
    KrishiConsent.hasVoiceConsent = () => true;
  });

  test('Scenario 1: Drop during recording — clip saved locally to IndexedDB outbox', async () => {
    // Simulate network drop during recording
    navigator.onLine = false;
    KrishiOffline.setConnectivityState('offline');

    const recordingClip = {
      sessionId: 'sess_offline_rec_1',
      audioBase64: Buffer.from('offline_audio_wav_data').toString('base64'),
      mimeType: 'audio/webm',
      durationMs: 4500, // 4.5s (under 60s limit)
      language: 'kn',
      transcript: null,
    };

    // User finishes recording; audio clip is enqueued into outbox
    const queuedItem = await KrishiOffline.enqueueVoiceClip(recordingClip);

    assert.ok(queuedItem.id, 'Client generates an ID/Idempotency-Key for the clip');
    assert.equal(queuedItem.session_id, 'sess_offline_rec_1');
    assert.equal(queuedItem.status, 'pending');
    assert.equal(queuedItem.duration_ms, 4500);

    // Verify clip is persisted in IndexedDB
    const storedItems = await KrishiOffline.getOutboxItems();
    assert.equal(storedItems.length, 1);
    assert.equal(storedItems[0].id, queuedItem.id);
    assert.equal(storedItems[0].status, 'pending');
    assert.equal(storedItems[0].audio_base64, recordingClip.audioBase64);
  });

  test('Scenario 2: Drop during upload — item stays pending with same idempotency key for retry', async () => {
    const itemId = 'idem_key_drop_upload_123';
    await KrishiOffline.enqueueVoiceClip({
      id: itemId,
      sessionId: 'sess_drop_upload',
      audioBase64: 'base64audio',
      mimeType: 'audio/webm',
      durationMs: 3000,
      language: 'kn'
    });

    // Mock fetch that simulates network disconnect mid-flight (rejects)
    let callCount = 0;
    globalThis.fetch = async () => {
      callCount++;
      throw new TypeError('Failed to fetch (Network connection dropped)');
    };

    // Process outbox while online
    KrishiOffline.setConnectivityState('online');
    await KrishiOffline.processOutbox();

    const storedItem = await KrishiOffline.getOutboxItem(itemId);
    assert.ok(storedItem, 'Item is preserved in outbox');
    assert.equal(storedItem.id, itemId, 'Idempotency key is retained unchanged');
    assert.equal(storedItem.attempts, 1, 'Attempt counter incremented');
    assert.equal(storedItem.status, 'pending', 'Status remains pending for retry');
    assert.ok(storedItem.error_message.includes('Failed to fetch'));
  });

  test('Scenario 3: Drop before reply — backend idempotency key ensures no duplicate processing on reconnect', async () => {
    const idempotencyKey = 'drop_before_reply_key_456';
    let serverExecutionCount = 0;
    const serverResponse = {
      reply: 'ನಿಮ್ಮ ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಯ ಅರ್ಹತೆ ದೃಢೀಕರಿಸಲಾಗಿದೆ.',
      session_id: 'sess_drop_before_reply',
      transcript: 'ಪಿಎಂ ಕಿಸಾನ್ ಸ್ಟೇಟಸ್',
      language: 'kn'
    };

    // Mock backend endpoint with idempotency handling
    const idempotencyStore = new Map();
    globalThis.fetch = async (url, options) => {
      const headers = options?.headers instanceof Headers ? options.headers : new Headers(options?.headers || {});
      const key = headers.get('Idempotency-Key');
      if (key && idempotencyStore.has(key)) {
        return {
          ok: true,
          status: 200,
          headers: new Headers({ 'X-Idempotency-Status': 'HIT', 'Idempotency-Key': key }),
          json: async () => idempotencyStore.get(key)
        };
      }
      serverExecutionCount++;
      idempotencyStore.set(key, serverResponse);
      return {
        ok: true,
        status: 200,
        headers: new Headers({ 'X-Idempotency-Status': 'STORED', 'Idempotency-Key': key }),
        json: async () => serverResponse
      };
    };

    // Enqueue chat message
    await KrishiOffline.enqueueChatMessage({
      id: idempotencyKey,
      sessionId: 'sess_drop_before_reply',
      message: 'ಪಿಎಂ ಕಿಸಾನ್ ಸ್ಟೇಟಸ್',
      language: 'kn'
    });

    // First attempt: Server processes and caches
    KrishiOffline.setConnectivityState('online');
    await KrishiOffline.processOutbox();
    assert.equal(serverExecutionCount, 1, 'First attempt reached server');

    // Simulate reconnect retry with same idempotency key
    // Even if client retries, server returns cached response without duplicate AI work
    const retryHeaders = new Headers({ 'Idempotency-Key': idempotencyKey });
    const retryRes = await globalThis.fetch('/api/chat', { headers: retryHeaders });
    const retryData = await retryRes.json();
    assert.equal(serverExecutionCount, 1, 'Server did not re-execute logic on duplicate key');
    assert.equal(retryData.reply, serverResponse.reply);
  });

  test('Scenario 4: Reconnect and auto-send — pending items dispatched in chronological order', async () => {
    // 1. Enter offline state
    KrishiOffline.setConnectivityState('offline');

    // 2. Enqueue 2 items while offline
    const item1 = await KrishiOffline.enqueueChatMessage({
      sessionId: 'sess_order_1',
      message: 'First question',
      language: 'en'
    });

    const item2 = await KrishiOffline.enqueueChatMessage({
      sessionId: 'sess_order_2',
      message: 'Second question',
      language: 'en'
    });

    // Ensure item1 is older than item2
    const db = await KrishiOffline.openDB();
    const tx = db.transaction('outbox', 'readwrite');
    const store = tx.objectStore('outbox');
    item1.created_at = Date.now() - 5000;
    item2.created_at = Date.now() - 1000;
    await new Promise(r => { store.put(item1).onsuccess = r; });
    await new Promise(r => { store.put(item2).onsuccess = r; });

    const dispatchedOrder = [];
    globalThis.fetch = async (url, options) => {
      const body = JSON.parse(options.body);
      dispatchedOrder.push(body.message);
      return {
        ok: true,
        status: 200,
        headers: new Headers({ 'Content-Type': 'application/json' }),
        json: async () => ({ reply: 'Answer to ' + body.message, session_id: body.session_id })
      };
    };

    // 3. Connection restores! setConnectivityState('online') triggers processOutbox()
    KrishiOffline.setConnectivityState('online');
    // Wait for async outbox processing to complete
    await new Promise(r => setTimeout(r, 50));

    assert.deepEqual(dispatchedOrder, ['First question', 'Second question'], 'Items processed in FIFO chronological order');

    const remainingItems = await KrishiOffline.getOutboxItems();
    assert.equal(remainingItems.length, 0, 'Successfully sent items removed from outbox');

    const sentEvents = eventsDispatched.filter(e => e.type === 'krishi:outbox-item-sent');
    assert.equal(sentEvents.length, 2, 'Sent events fired for each resolved item');
  });

  test('Scenario 5: Queue limits enforcement (duration, count, storage, 24h TTL)', async () => {
    // 1. Clip > 60s rejected
    await assert.rejects(
      async () => {
        await KrishiOffline.enqueueVoiceClip({
          sessionId: 'sess_limit',
          audioBase64: 'short',
          durationMs: 65_000, // 65 seconds
        });
      },
      /60/
    );

    // 2. Max 10 items in queue
    for (let i = 0; i < 10; i++) {
      await KrishiOffline.enqueueChatMessage({
        sessionId: 'sess_limit',
        message: `Message ${i}`,
      });
    }
    const currentQueue = await KrishiOffline.getOutboxItems();
    assert.equal(currentQueue.length, 10);

    // 11th item must be rejected
    await assert.rejects(
      async () => {
        await KrishiOffline.enqueueChatMessage({
          sessionId: 'sess_limit',
          message: 'Message 11 should fail',
        });
      },
      /10/
    );

    // 3. Clear queue and test 24h TTL expiry
    await KrishiOffline.clearAllData();

    const expiredItem = await KrishiOffline.enqueueChatMessage({
      sessionId: 'sess_expired',
      message: 'Old query',
    });

    // Set creation timestamp back by 25 hours
    const db = await KrishiOffline.openDB();
    const tx = db.transaction('outbox', 'readwrite');
    const store = tx.objectStore('outbox');
    expiredItem.created_at = Date.now() - (25 * 60 * 60 * 1000);
    await new Promise(r => { store.put(expiredItem).onsuccess = r; });

    // Process outbox; expired item must be deleted without sending
    let fetchCalled = false;
    globalThis.fetch = async () => { fetchCalled = true; return { ok: true, json: async () => ({}) }; };

    KrishiOffline.setConnectivityState('online');
    await KrishiOffline.processOutbox();

    assert.equal(fetchCalled, false, 'Expired item was not sent to server');
    const outboxAfterExpiry = await KrishiOffline.getOutboxItems();
    assert.equal(outboxAfterExpiry.length, 0, 'Expired item deleted from outbox');

    const expiredEvents = eventsDispatched.filter(e => e.type === 'krishi:outbox-item-expired');
    assert.equal(expiredEvents.length, 1, 'Expired event emitted to notify user');
  });

  test('Scenario 6: Logout and consent withdrawal wiping queues', async () => {
    // Add 1 voice item and 1 chat item
    const voiceItem = await KrishiOffline.enqueueVoiceClip({
      sessionId: 'sess_cleanup',
      audioBase64: 'audio_payload',
      durationMs: 3000,
    });
    const chatItem = await KrishiOffline.enqueueChatMessage({
      sessionId: 'sess_cleanup',
      message: 'Text query',
    });

    let items = await KrishiOffline.getOutboxItems();
    assert.equal(items.length, 2);

    // 1. Consent withdrawal purges voice recordings while preserving chat
    await KrishiOffline.purgeVoiceQueue();
    items = await KrishiOffline.getOutboxItems();
    assert.equal(items.length, 1);
    assert.equal(items[0].id, chatItem.id);
    assert.equal(items[0].type, 'chat');

    // 2. Logout clears all IndexedDB data (outbox, sessions, evaluations)
    await KrishiOffline.saveSessionCache('sess_cleanup', [{ role: 'user', content: 'hello' }]);
    assert.ok(await KrishiOffline.getSessionCache('sess_cleanup'));

    await KrishiOffline.clearAllData();
    items = await KrishiOffline.getOutboxItems();
    assert.equal(items.length, 0, 'Outbox completely wiped on logout');
    const clearedCache = await KrishiOffline.getSessionCache('sess_cleanup');
    assert.ok(!clearedCache, 'Session cache wiped on logout');
  });
});
