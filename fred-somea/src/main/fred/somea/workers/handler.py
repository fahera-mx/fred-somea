import os
import json

from fred.dao.service.catalog import ServiceCatalog
from fred.worker.interface import HandlerInterface
from fred.somea.sync.catalog import SyncCatalog
from fred.settings import (
    get_environ_variable,
    logger_manager,
)

logger = logger_manager.get_logger(__name__)


@dataclass(frozen=True, slots=False)
class HandlerSocialMediaSync(HandlerInterface):

    def __post_init__(self):
        # Call parent post-init to ensure context is set up
        super().__post_init__()

    def handler(self, payload: dict) -> dict:
        sm_type = payload.pop("sm_type").upper()
        sm_instance_configs = payload.pop("sm_instance_configs", {})
        sm_sync_configs = payload.pop("sm_sync_configs")
        with SyncCatalog[sm_type.upper()].auto(**sm_instance_configs) as sm:
            out = sm.sync(
                disable_zip=False,
                **sm_sync_configs,
            )
        output_filepath = out.sync_compressed_filepath
        if not os.path.exists(output_filepath):
            error_msg = f"Output file does not exists: {output_filepath}"
            logger.error(error_msg)
            return {
                "ok": False,
                "message": error_msg,
            }
        match payload.pop("output_type", "filesystem").upper():
            case "FILESYSTEM":
                logger.info("Output Type: Filesystem (done)")
            case "MINIO":
                # Get the bucketname from the payload => environ => default
                minio_bucket = payload.pop(
                    "minio_bucket",
                    get_environ_variable(
                        "SOMEA_BUCKET_NAME",
                        default=f"fred-somea-{sm_type.lower()}"
                    )
                )
                minio_service = ServiceCatalog.MINIO.auto(**payload.pop("minio_configs", {}))
                # Create bucket if not exists
                if not minio_service.bucket_exists(bucket_name=minio_bucket):
                    logger.warning(f"Creating bucket: {minio_bucket}")
                    minio_service.client.make_bucket(minio_bucket)
                # Upload main snapshot (zip) into MinIO
                logger.info("Register the main snapshot for user {out.username} in MinIO...")
                minio_service.client.fput_object(
                    bucket_name=minio_bucket,
                    object_name=os.path.join(
                        out.username,
                        "snapshots",
                        out.sync_compressed_filename,
                    ),
                    file_path=out.sync_compressed_filepath,
                )
                username_dirpath = out.username_dirpath
                logger.info("Register the individual assets for user {out.username} in MinIO...")
                for image_filename in os.listdir(username_dirpath):
                    if not image_filename.endswith(".jpg"):
                        continue
                    image_filepath = os.path.join(username_dirpath, image_filename)
                    prefix, *_ = image_filename.split("UTC")
                    yyyy, mm, dd, *_ = image_filename.split("-")
                    meta_filepath = os.path.join(username_dirpath, f"{prefix}UTC.json")
                    if not os.path.exists(meta_filepath):
                        logger.warning(f"Meta file does not exist for image: {image_filepath}")
                        continue
                    with open(meta_filepath, "r") as mh:
                        content = mh.read()
                    meta_payload = json.loads(content)
                    asset_id = meta_payload["node"]["id"]
                    asset_type = meta_payload["instaloader"]["node_type"]
                    asset_filename = f"{yyyy}-{mm}-{dd}-{asset_type}-{out.username}-{asset_id}.jpg"
                    minio_service.client.fput_object(
                        bucket_name=minio_bucket,
                        object_name=os.path.join(
                            out.username,
                            "assets",
                            asset_filename,
                        ),
                        file_path=image_filepath,
                    )

        return {
            "ok": True,
            "output": {
                "username": out.username,
                "filename": out.filename,
                "run_id": out.run_id,
                "run_at": out.run_at,
            }
        }
