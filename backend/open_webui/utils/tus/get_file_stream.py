from fastapi.responses import StreamingResponse
from open_webui.models.files import FileModel


async def get_file(file: FileModel, file_path: str, headers: dict, content_type: str):

    def read_file(buffering=10 * 1024 * 1024):
        f = open(file_path, "rb", buffering=buffering)
        while True:
            chunk = f.read(buffering)
            if not chunk:
                break
            yield chunk

    if file.filename:
        headers = {"Content-Disposition": f'attachment; filename="{file.filename}"'}

        import mimetypes

        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type:
            return StreamingResponse(read_file(), media_type=mime_type, headers=headers)

        if content_type:
            return StreamingResponse(
                read_file(), media_type=content_type, headers=headers
            )

        return StreamingResponse(read_file(), headers=headers)

    return StreamingResponse(read_file(), media_type="video/mp4")
