import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
import * as tus from 'tus-js-client'


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

async function uploadFileTUS(file: File, metadata?: object | null) {
	return new Promise((resolve, reject) => {
		let chunkSize = 20 * 1024 * 1024; // 20MB chunk size
		console.info("chunkSize:", chunkSize, "%");
		let percentageView = 0;
		const upload = new tus.Upload(file, {
			endpoint: `${WEBUI_BASE_URL}${WEBUI_API_BASE_URL}/files/tus`, // Replace with your tus server URL
			headers: { Authorization: `Bearer ${localStorage.token}` },
			retryDelays: [0, 3000, 5000, 10000, 20000],
			chunkSize: chunkSize, // 50MB chunk size
			metadata: {
				filename: file.name,
				filetype: file.type,
				filesize: file.size,
				'uploadType': 'direct',
				'metadata': JSON.stringify(metadata)
			},
			onError: (error) => {
				console.error("Failed because: " + error);
				reject(error);
			},
			onProgress: (bytesSent, bytesTotal) => {
				if (Math.abs(percentageView - bytesSent / bytesTotal * 100) >= 1) {
					const percentage = (bytesSent / bytesTotal * 100).toFixed(2);
					console.info(bytesSent, bytesTotal, percentage + "%");
					percentageView = bytesSent / bytesTotal * 100
				}
			},
			onSuccess: () => {
				console.info("Upload finished:", upload.url);
				resolve(upload.url);
			}
		});

		// Start the upload
		// upload.start();
		upload.findPreviousUploads().then((previousUploads) => {
			// Found previous uploads so we select the first one.
			if (previousUploads.length) {
				upload.resumeFromPreviousUpload(previousUploads[0]);
				console.info("Continue upload:", previousUploads[0]);
			}

			// Start the upload
			upload.start();
		})

	});
}

export const uploadDirectFile = async (file: File, metadata?: object | null) => {
	let error = null;	
	let uploadedUrl = '';

    if (file) {
        // const upload = new Upload(file, {
        try {
			console.info("File uploaded successfully to:", uploadedUrl);
			uploadedUrl = await uploadFileTUS(file, metadata);
		} catch (err) {
			console.error("Upload failed:", err);
			error = err;
		}
        console.info('Upload finished 2:', uploadedUrl);

    } else {
        console.warn('No file selected.');
    }

	if (error) {
		console.error(error);
		throw error;
	}

	const fileMetadata = {
		'filename': file.name,
		'filetype': file.type,
		'filesize': file.size,
		'data': metadata,
		'fileURL': uploadedUrl
	};

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/tusdone`, {
		method: 'POST',
		headers: {
			Accept: 'application/json', 
			'Content-Type': 'application/json',
			authorization: `Bearer ${localStorage.token}`
		},
		body: JSON.stringify(fileMetadata)
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

	console.info('res: ', res);
	return res;
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
