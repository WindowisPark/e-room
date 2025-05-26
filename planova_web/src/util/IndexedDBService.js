class IndexedDBService {
  constructor() {
    this.dbName = 'PDFDatabase';
    this.version = 1;
    this.storeName = 'files';
  }

  async openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      
      request.onerror = () => {
        console.error('IndexedDB 열기 실패:', request.error);
        reject(request.error);
      };
      
      request.onsuccess = () => {
        console.log('IndexedDB 열기 성공');
        resolve(request.result);
      };
      
      request.onupgradeneeded = (event) => {
        console.log('IndexedDB 초기화 중...');
        const db = event.target.result;
        
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: 'id' });
          store.createIndex('name', 'name', { unique: false });
          store.createIndex('parentId', 'parentId', { unique: false });
          console.log('Object Store 생성 완료');
        }
      };
    });
  }

  async saveFile(fileInfo) {
    try {
      const db = await this.openDB();
      const transaction = db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      
      return new Promise((resolve, reject) => {
        const request = store.put(fileInfo);
        
        request.onsuccess = () => {
          console.log('파일 저장 성공:', fileInfo.id);
          resolve(fileInfo.id);
        };
        
        request.onerror = () => {
          console.error('파일 저장 실패:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('IndexedDB 저장 오류:', error);
      throw error;
    }
  }

  async getFile(fileId) {
    try {
      const db = await this.openDB();
      const transaction = db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      
      return new Promise((resolve, reject) => {
        const request = store.get(fileId);
        
        request.onsuccess = () => {
          console.log('파일 읽기 성공:', fileId);
          resolve(request.result);
        };
        
        request.onerror = () => {
          console.error('파일 읽기 실패:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('IndexedDB 읽기 오류:', error);
      throw error;
    }
  }

  async getAllFiles() {
    try {
      const db = await this.openDB();
      const transaction = db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      
      return new Promise((resolve, reject) => {
        const request = store.getAll();
        
        request.onsuccess = () => {
          console.log('전체 파일 목록 읽기 성공:', request.result.length + '개');
          resolve(request.result);
        };
        
        request.onerror = () => {
          console.error('전체 파일 목록 읽기 실패:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('IndexedDB 전체 읽기 오류:', error);
      throw error;
    }
  }

  async deleteFile(fileId) {
    try {
      const db = await this.openDB();
      const transaction = db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      
      return new Promise((resolve, reject) => {
        const request = store.delete(fileId);
        
        request.onsuccess = () => {
          console.log('파일 삭제 성공:', fileId);
          resolve(true);
        };
        
        request.onerror = () => {
          console.error('파일 삭제 실패:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('IndexedDB 삭제 오류:', error);
      throw error;
    }
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

export default new IndexedDBService();