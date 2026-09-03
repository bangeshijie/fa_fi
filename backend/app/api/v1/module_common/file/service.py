from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.config.setting import settings
from app.core.base_schema import DownloadFileSchema, UploadResponseSchema
from app.core.exceptions import CustomException
from app.core.logger import log
from app.utils.upload_util import UploadUtil


class FileService:
    """
    文件管理服务层
    """

    @classmethod
    async def upload_service(
        cls,
        base_url: str,
        file: UploadFile,
        upload_type: str = "file",
        target_path: str | None = None,
    ) -> dict:
        """
        上传文件。

        参数:
        - base_url (str): 基础访问 URL。
        - file (UploadFile): 上传文件对象。
        - upload_type (str): 上传类型，'file'、'avatar'、'param'、'resource'，默认 'file'。
        - target_path (str | None): 目标目录路径，仅 resource 类型支持。

        返回:
        - Dict: 上传响应字典。

        异常:
        - CustomException: 当未选择文件或上传类型错误时抛出。
        """
        if upload_type == "avatar":
            extension = Path(file.filename or "").suffix.lower()
            if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise CustomException(msg="头像仅支持 JPG、PNG、WEBP 格式")

        filename, filepath, _file_url = await UploadUtil.upload_file(
            file=file,
            base_url=base_url,
            upload_type=upload_type,
            target_path=target_path,
        )

        if upload_type == "avatar":
            try:
                with Image.open(filepath) as image:
                    image.verify()
            except (UnidentifiedImageError, OSError) as exc:
                UploadUtil.delete_file(filepath)
                raise CustomException(msg="上传文件不是有效的图片") from exc

        public_path = cls._to_public_path(filepath)

        return UploadResponseSchema(
            file_path=public_path,
            file_name=filename,
            origin_name=file.filename,
            file_url=public_path,
        ).model_dump()

    @staticmethod
    def _to_public_path(filepath: Path) -> str:
        """将磁盘路径转换成可持久化的静态资源路径。"""
        static_root = settings.STATIC_ROOT.resolve()
        path = filepath.resolve()
        try:
            relative = path.relative_to(static_root).as_posix()
        except ValueError as exc:
            raise CustomException(msg="上传文件路径不在静态资源目录内") from exc
        return f"{settings.STATIC_URL.rstrip('/')}/{relative}"

    @staticmethod
    def _to_disk_path(file_path: str) -> Path:
        """将公开路径、相对路径或物理路径统一转换成磁盘路径。"""
        normalized = file_path.strip().replace("\\", "/")
        static_url = settings.STATIC_URL.rstrip("/")
        static_dir = settings.STATIC_DIR.strip("/").replace("\\", "/")

        if normalized.startswith(f"{static_url}/"):
            relative = normalized[len(static_url) + 1 :]
            return settings.STATIC_ROOT.joinpath(*relative.split("/"))
        if normalized == static_dir or normalized.startswith(f"{static_dir}/"):
            return settings.STATIC_ROOT.parent.joinpath(*normalized.split("/"))
        return Path(normalized)

    @classmethod
    def _validate_download_path(cls, file_path: str) -> str:
        """
        验证下载路径是否安全。

        参数:
        - file_path (str): 文件路径。

        返回:
        - str: 安全的绝对路径字符串。

        异常:
        - CustomException: 当路径不安全时抛出。
        """
        if not file_path:
            raise CustomException(msg="请选择要下载的文件")

        dangerous_patterns = ["../", "..\\", "\0"]
        for pattern in dangerous_patterns:
            if pattern in file_path:
                log.error(f"检测到路径穿越攻击: {file_path}")
                raise CustomException(msg="非法的文件路径")

        upload_root = settings.UPLOAD_FILE_PATH.resolve()
        abs_path = cls._to_disk_path(file_path).resolve()

        if not abs_path.is_relative_to(upload_root):
            log.error(f"路径不在上传目录内: {file_path}")
            raise CustomException(msg="非法的文件路径")

        return str(abs_path)  # 返回字符串

    @classmethod
    async def download_service(cls, file_path: str) -> DownloadFileSchema:
        """
        下载文件。
        """
        safe_path: str = cls._validate_download_path(file_path)  # 返回 str

        # 直接使用字符串
        if not UploadUtil.check_file_exists(safe_path):
            raise CustomException(msg="文件不存在")

        file_name = await UploadUtil.download_file(safe_path)

        return DownloadFileSchema(
            file_path=safe_path,
            file_name=str(file_name),
        )
