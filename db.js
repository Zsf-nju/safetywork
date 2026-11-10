const request = req => new Promise((resolve, reject) => { req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error); });
export async function openDB() {
  const req = indexedDB.open('safetywork-v1', 1);
  req.onupgradeneeded = () => {
    req.result.createObjectStore('workspace');
    req.result.createObjectStore('pdfs');
  };
  return request(req);
}
export async function read(db, store, key) { return request(db.transaction(store).objectStore(store).get(key)); }
export async function write(db, state, pdfChanges = []) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(['workspace', 'pdfs'], 'readwrite');
    tx.objectStore('workspace').put(state, 'state');
    for (const change of pdfChanges) {
      if (change.remove) tx.objectStore('pdfs').delete(change.id);
      else tx.objectStore('pdfs').put(change.blob, change.id);
    }
    tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error);
  });
}
