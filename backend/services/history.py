import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class HistoryService:
    def __init__(self):
        self.history_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "history"
        )
        os.makedirs(self.history_dir, exist_ok=True)

        self.index_file = os.path.join(self.history_dir, "index.json")
        self._init_index()

    def _init_index(self):
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump({"records": []}, f, ensure_ascii=False, indent=2)

    def _load_index(self) -> Dict:
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"records": []}

    def _save_index(self, index: Dict):
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _get_record_path(self, record_id: str) -> str:
        return os.path.join(self.history_dir, f"{record_id}.json")

    def create_record(
        self,
        topic: str,
        outline: Dict,
        task_id: Optional[str] = None
    ) -> str:
        record_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        record = {
            "id": record_id,
            "title": topic,
            "created_at": now,
            "updated_at": now,
            "outline": outline,
            "images": {
                "task_id": task_id,
                "generated": []
            },
            "status": "draft",  # draft/generating/completed/partial
            "thumbnail": None
        }

        record_path = self._get_record_path(record_id)
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        index = self._load_index()
        index["records"].insert(0, {
            "id": record_id,
            "title": topic,
            "created_at": now,
            "updated_at": now,
            "status": "draft",
            "thumbnail": None,
            "page_count": len(outline.get("pages", [])),
            "task_id": task_id
        })
        self._save_index(index)

        return record_id

    def get_record(self, record_id: str) -> Optional[Dict]:
        record_path = self._get_record_path(record_id)

        if not os.path.exists(record_path):
            return None

        try:
            with open(record_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def update_record(
        self,
        record_id: str,
        outline: Optional[Dict] = None,
        images: Optional[Dict] = None,
        status: Optional[str] = None,
        thumbnail: Optional[str] = None
    ) -> bool:
        record = self.get_record(record_id)
        if not record:
            return False

        now = datetime.now().isoformat()
        record["updated_at"] = now

        if outline is not None:
            record["outline"] = outline

        if images is not None:
            record["images"] = images

        if status is not None:
            record["status"] = status

        if thumbnail is not None:
            record["thumbnail"] = thumbnail

        record_path = self._get_record_path(record_id)
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        index = self._load_index()
        for idx_record in index["records"]:
            if idx_record["id"] == record_id:
                idx_record["updated_at"] = now
                if status:
                    idx_record["status"] = status
                if thumbnail:
                    idx_record["thumbnail"] = thumbnail
                if outline:
                    idx_record["page_count"] = len(outline.get("pages", []))
                if images is not None and images.get("task_id"):
                    idx_record["task_id"] = images.get("task_id")
                break

        self._save_index(index)
        return True

    def delete_record(self, record_id: str) -> bool:
        record = self.get_record(record_id)
        if not record:
            return False

        # 删除任务图片目录
        if record.get("images") and record["images"].get("task_id"):
            task_id = record["images"]["task_id"]
            task_dir = os.path.join(self.history_dir, task_id)
            if os.path.exists(task_dir) and os.path.isdir(task_dir):
                try:
                    import shutil
                    shutil.rmtree(task_dir)
                    print(f"已删除任务目录: {task_dir}")
                except Exception as e:
                    print(f"删除任务目录失败: {task_dir}, {e}")

        # 删除记录JSON文件
        record_path = self._get_record_path(record_id)
        try:
            os.remove(record_path)
        except Exception:
            return False

        # 更新索引
        index = self._load_index()
        index["records"] = [r for r in index["records"] if r["id"] != record_id]
        self._save_index(index)

        return True

    def list_records(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict:
        index = self._load_index()
        records = index.get("records", [])

        if status:
            records = [r for r in records if r.get("status") == status]

        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size
        page_records = records[start:end]

        return {
            "records": page_records,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    def search_records(self, keyword: str) -> List[Dict]:
        index = self._load_index()
        records = index.get("records", [])

        keyword_lower = keyword.lower()
        results = [
            r for r in records
            if keyword_lower in r.get("title", "").lower()
        ]

        return results

    def get_statistics(self) -> Dict:
        index = self._load_index()
        records = index.get("records", [])

        total = len(records)
        status_count = {}

        for record in records:
            status = record.get("status", "draft")
            status_count[status] = status_count.get(status, 0) + 1

        return {
            "total": total,
            "by_status": status_count
        }

    def scan_and_sync_task_images(self, task_id: str) -> Dict[str, Any]:
        """
        扫描任务文件夹，同步图片列表

        Args:
            task_id: 任务ID

        Returns:
            扫描结果
        """
        task_dir = os.path.join(self.history_dir, task_id)

        if not os.path.exists(task_dir) or not os.path.isdir(task_dir):
            return {
                "success": False,
                "error": f"任务目录不存在: {task_id}"
            }

        try:
            # 扫描目录下所有图片文件（排除缩略图）
            image_files = []
            for filename in os.listdir(task_dir):
                # 跳过缩略图文件（以 thumb_ 开头）
                if filename.startswith('thumb_'):
                    continue
                if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    image_files.append(filename)

            # 按文件名排序（数字排序）
            def get_index(filename):
                try:
                    return int(filename.split('.')[0])
                except:
                    return 999

            image_files.sort(key=get_index)

            # 查找关联的历史记录
            index = self._load_index()
            record_id = None
            for rec in index.get("records", []):
                # 通过遍历所有记录，找到 task_id 匹配的记录
                record_detail = self.get_record(rec["id"])
                if record_detail and record_detail.get("images", {}).get("task_id") == task_id:
                    record_id = rec["id"]
                    break

            if record_id:
                # 更新历史记录
                record = self.get_record(record_id)
                if record:
                    # 判断状态
                    expected_count = len(record.get("outline", {}).get("pages", []))
                    actual_count = len(image_files)

                    if actual_count == 0:
                        status = "draft"
                    elif actual_count >= expected_count:
                        status = "completed"
                    else:
                        status = "partial"

                    # 更新图片列表和状态
                    self.update_record(
                        record_id,
                        images={
                            "task_id": task_id,
                            "generated": image_files
                        },
                        status=status,
                        thumbnail=image_files[0] if image_files else None
                    )

                    return {
                        "success": True,
                        "record_id": record_id,
                        "task_id": task_id,
                        "images_count": len(image_files),
                        "images": image_files,
                        "status": status
                    }

            # 没有关联的记录，返回扫描结果
            return {
                "success": True,
                "task_id": task_id,
                "images_count": len(image_files),
                "images": image_files,
                "no_record": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"扫描任务失败: {str(e)}"
            }

    def scan_all_tasks(self) -> Dict[str, Any]:
        """
        扫描所有任务文件夹，同步图片列表

        Returns:
            扫描结果统计
        """
        if not os.path.exists(self.history_dir):
            return {
                "success": False,
                "error": "历史记录目录不存在"
            }

        try:
            synced_count = 0
            failed_count = 0
            orphan_tasks = []  # 没有关联记录的任务
            results = []

            # 遍历 history 目录
            for item in os.listdir(self.history_dir):
                item_path = os.path.join(self.history_dir, item)

                # 只处理目录（任务文件夹）
                if not os.path.isdir(item_path):
                    continue

                # 假设任务文件夹名就是 task_id
                task_id = item

                # 扫描并同步
                result = self.scan_and_sync_task_images(task_id)
                results.append(result)

                if result.get("success"):
                    if result.get("no_record"):
                        orphan_tasks.append(task_id)
                    else:
                        synced_count += 1
                else:
                    failed_count += 1

            return {
                "success": True,
                "total_tasks": len(results),
                "synced": synced_count,
                "failed": failed_count,
                "orphan_tasks": orphan_tasks,
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"扫描所有任务失败: {str(e)}"
            }


_service_instance = None


def get_history_service() -> HistoryService:
    global _service_instance
    if _service_instance is None:
        _service_instance = HistoryService()
    return _service_instance
