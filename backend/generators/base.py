"""图片生成器抽象基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ImageGeneratorBase(ABC):
    """图片生成器抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化生成器

        Args:
            config: 配置字典
        """
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        **kwargs
    ) -> bytes:
        """
        生成图片

        Args:
            prompt: 提示词
            **kwargs: 其他参数（如分辨率、宽高比等）

        Returns:
            图片二进制数据
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            配置是否有效
        """
        pass

    def get_supported_sizes(self) -> list:
        """
        获取支持的图片尺寸

        Returns:
            支持的尺寸列表
        """
        return self.config.get('supported_sizes', ['1024x1024'])

    def get_supported_aspect_ratios(self) -> list:
        """
        获取支持的宽高比

        Returns:
            支持的宽高比列表
        """
        return self.config.get('supported_aspect_ratios', ['1:1', '3:4', '16:9'])
