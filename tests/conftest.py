"""
pytest 配置和共享 fixtures
"""
import os
import sys
import pytest
import tempfile
import shutil

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """创建测试用 Flask 应用"""
    from backend.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def temp_history_dir():
    """创建临时历史目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_pages():
    """示例页面数据"""
    return [
        {"index": 0, "type": "cover", "content": "测试封面内容"},
        {"index": 1, "type": "content", "content": "测试内容页1"},
        {"index": 2, "type": "content", "content": "测试内容页2"},
        {"index": 3, "type": "summary", "content": "测试总结页"}
    ]


@pytest.fixture
def sample_outline():
    """示例大纲数据"""
    return {
        "raw": "这是原始大纲文本",
        "pages": [
            {"index": 0, "type": "cover", "content": "封面：秋季穿搭指南"},
            {"index": 1, "type": "content", "content": "内容1：基础款搭配"},
            {"index": 2, "type": "summary", "content": "总结：穿搭要点"}
        ]
    }


@pytest.fixture
def sample_history_record():
    """示例历史记录"""
    return {
        "id": "test-record-001",
        "title": "测试记录标题",
        "status": "completed",
        "outline": {
            "raw": "原始大纲",
            "pages": [
                {"index": 0, "type": "cover", "content": "封面内容"}
            ]
        },
        "images": {
            "task_id": "task_12345678",
            "generated": ["0.png"]
        },
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    }
