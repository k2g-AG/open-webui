import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
import * as tus from 'tus-js-client';

export const uploadFile = async (token: string, file: File, metadata?: object | null) => {
	const data = new FormData();
	data.append('file', file);
	if (metadata) {
		data.append('metadata', JSON.stringify(metadata));
	}

	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		},
		body: data
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

const tusUploads = new Map<string, tus.Upload>(); // itemId -> upload

type TusCallbacks = {
	itemId: string; // <-- connect to the UI item
	onProgress?: (pct: number, sent: number, total: number) => void;
	onRegister?: (upload: tus.Upload) => void; // optional hook
};

export function uploadFileTUS(file: File, metadata?: object | null, cbs?: TusCallbacks) {
	return new Promise<string>((resolve, reject) => {
		let percentageView = 0;

		const upload = new tus.Upload(file, {
			endpoint: `${WEBUI_BASE_URL}${WEBUI_API_BASE_URL}/files/tus`,
			headers: { Authorization: `Bearer ${localStorage.token}` },
			retryDelays: [0, 3000, 5000, 10000, 20000],
			chunkSize: 20 * 1024 * 1024, // 20MB
			metadata: {
				filename: file.name,
				filetype: file.type,
				filesize: String(file.size),
				uploadType: 'direct',
				metadata: JSON.stringify(metadata ?? {})
			},
			onError: (error) => {
				tusUploads.delete(cbs?.itemId ?? '');
				reject(error);
			},
			onProgress: (bytesSent, bytesTotal) => {
				const pct = Number(((bytesSent / bytesTotal) * 100).toFixed(2));
				if (Math.abs(percentageView - pct) >= 1) {
					percentageView = pct;
					cbs?.onProgress?.(pct, bytesSent, bytesTotal);
				}
			},
			onSuccess: () => {
				const url = upload.url!;
				tusUploads.delete(cbs?.itemId ?? '');
				resolve(url);
			}
		});

		// Save / expose instance so we can cancel per file
		if (cbs?.itemId) tusUploads.set(cbs.itemId, upload);
		cbs?.onRegister?.(upload);

		upload.findPreviousUploads().then((prev) => {
			if (prev.length) upload.resumeFromPreviousUpload(prev[0]);
			upload.start();
		});
	});
}

export function cancelUploadByItemId(itemId: string) {
	const up = tusUploads.get(itemId);
	if (up) {
		up.abort(true);
		tusUploads.delete(itemId);
		console.warn('Upload cancelled for item:', itemId);
	}
}

export const uploadDirectFile = async (
	file: File,
	metadata?: object | null,
	cbs?: TusCallbacks
) => {
	let uploadedUrl = '';
	try {
		uploadedUrl = await uploadFileTUS(file, metadata, cbs);
	} catch (err) {
		throw err;
	}

	const body = {
		filename: file.name,
		filetype: file.type,
		filesize: file.size,
		data: JSON.stringify(metadata ?? {}),
		fileURL: uploadedUrl
	};

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/tusdone`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${localStorage.token}`
		},
		body: JSON.stringify(body)
	});

	if (!res.ok) throw await res.json();
	return res.json();
};

export const uploadDirectFileOld = async (token: string, file: File, metadata?: object | null) => {
	const data = new FormData();
	data.append('file', file);
	if (metadata) {
		data.append('metadata', JSON.stringify(metadata));
	}

	data.append('uploadType', 'direct');

	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		},
		body: data
	})
		.then(async (res) => {
			console.log(res);
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		console.error(error);
		throw error;
	}

	console.warn('res: ', res);
	return res;
};

export const uploadDir = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/upload/dir`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getFiles = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getFileById = async (token: string, id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${id}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateFileDataContentById = async (token: string, id: string, content: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${id}/data/content/update`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			content: content
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getFileContentById = async (id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${id}/content`, {
		method: 'GET',
		headers: {
			Accept: 'application/json'
		},
		credentials: 'include'
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.blob();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);

			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteFileById = async (token: string, id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${id}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteAllFiles = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/all`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
