"""
状态管理器
管理 features.json 和 progress.md
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class StateManager:
    """管理项目状态和进度"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(".")
        self.features_file = self.base_dir / "features.json"
        self.progress_file = self.base_dir / "progress.md"

    def load_features(self) -> dict:
        """加载功能排期表"""
        if self.features_file.exists():
            return json.loads(self.features_file.read_text(encoding="utf-8"))
        return {"features": []}

    def save_features(self, data: dict):
        """保存功能排期表"""
        self.features_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def update_feature_status(self, feature_id: str, status: str):
        """更新功能状态"""
        data = self.load_features()
        for feature in data.get("features", []):
            if feature["id"] == feature_id:
                feature["status"] = status
                break
        self.save_features(data)

    def append_progress(self, entry: str, section: str = "决策记录"):
        """追加决策日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = f"\n### [{timestamp}] {section}\n{entry}\n"

        if self.progress_file.exists():
            content = self.progress_file.read_text(encoding="utf-8")
        else:
            content = "# 决策日志\n"

        # 在文件末尾追加
        self.progress_file.write_text(
            content + new_entry,
            encoding="utf-8"
        )

    def get_next_pending_feature(self) -> Optional[dict]:
        """获取下一个待处理的功能"""
        data = self.load_features()
        for feature in data.get("features", []):
            if feature.get("status") == "pending":
                return feature
        return None
