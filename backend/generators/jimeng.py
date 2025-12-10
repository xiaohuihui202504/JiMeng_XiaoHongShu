"""即梦4.5图片生成器"""
import logging
import time
import random
import json
from functools import wraps
from typing import Dict, Any, Optional, List
import requests
from .base import ImageGeneratorBase

logger = logging.getLogger(__name__)

# API 支持的比例列表
SUPPORTED_RATIOS = ["1:1", "4:3", "3:4", "16:9", "9:16"]

# 尺寸到比例的映射
SIZE_TO_RATIO = {
    "1536x864": "16:9",
    "864x1536": "9:16",
    "1024x1024": "1:1",
    "1152x864": "4:3",
    "864x1152": "3:4",
    "1280x720": "16:9",
    "720x1280": "9:16",
}

# 默认比例和分辨率
DEFAULT_RATIO = "4:3"
DEFAULT_RESOLUTION = "2k"

# Prompt 最大长度（字符数）
MAX_PROMPT_LENGTH = 1500


def retry_on_error(max_retries=5, base_delay=3):
    """错误自动重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    # 检查是否是速率限制错误
                    if "429" in error_str or "rate" in error_str.lower():
                        if attempt < max_retries - 1:
                            wait_time = (base_delay ** attempt) + random.uniform(0, 1)
                            logger.warning(f"遇到速率限制，{wait_time:.1f}秒后重试 (尝试 {attempt + 2}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                    # 其他错误或重试耗尽
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"请求失败: {error_str[:100]}，{wait_time}秒后重试")
                        time.sleep(wait_time)
                        continue
                    raise
            logger.error(f"图片生成失败: 重试 {max_retries} 次后仍失败")
            raise Exception(
                f"图片生成失败：重试 {max_retries} 次后仍失败。\n"
                "可能原因：\n"
                "1. API持续限流或配额不足\n"
                "2. 网络连接持续不稳定\n"
                "3. API服务暂时不可用\n"
                "建议：稍后再试，或检查API配额和网络状态"
            )
        return wrapper
    return decorator


class JiMengGenerator(ImageGeneratorBase):
    """即梦4.5图片生成器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        logger.debug("初始化 JiMengGenerator...")

        if not self.api_key:
            logger.error("即梦 API Key 未配置")
            raise ValueError(
                "即梦 API Key 未配置。\n"
                "解决方案：在系统设置页面编辑该服务商，填写 API Key"
            )

        if not self.base_url:
            logger.error("即梦 API Base URL 未配置")
            raise ValueError(
                "即梦 API Base URL 未配置。\n"
                "解决方案：在系统设置页面编辑该服务商，填写 Base URL"
            )

        # 规范化 base_url
        self.base_url = self.base_url.rstrip('/')

        # 默认模型
        self.default_model = config.get('model', 'jimeng-4.5')

        logger.info(f"JiMengGenerator 初始化完成: base_url={self.base_url}, model={self.default_model}")

    def _clean_prompt(self, prompt: str) -> str:
        """清理和标准化提示词"""
        if not isinstance(prompt, str):
            prompt = str(prompt)

        # 移除可能导致问题的字符
        cleaned = prompt.strip()

        # 替换可能有问题的字符
        cleaned = cleaned.replace('\x00', '')  # 移除null字符
        cleaned = cleaned.replace('\r\n', '\n')  # 统一换行符
        cleaned = cleaned.replace('\r', '\n')

        # 移除过多的连续换行
        while '\n\n\n' in cleaned:
            cleaned = cleaned.replace('\n\n\n', '\n\n')

        # 移除过多的连续空格
        while '  ' in cleaned:
            cleaned = cleaned.replace('  ', ' ')

        return cleaned

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.api_key and self.base_url)

    def _size_to_ratio(self, size: str) -> str:
        """将尺寸转换为支持的比例"""
        if size in SIZE_TO_RATIO:
            ratio = SIZE_TO_RATIO[size]
            # 验证是否在支持列表中
            if ratio in SUPPORTED_RATIOS:
                return ratio
        # 尝试解析尺寸计算比例
        try:
            width, height = map(int, size.split('x'))
            # 计算最简比例
            from math import gcd
            g = gcd(width, height)
            w, h = width // g, height // g
            ratio = f"{w}:{h}"
            if ratio in SUPPORTED_RATIOS:
                return ratio
        except Exception:
            pass
        # 默认返回 4:3
        logger.warning(f"尺寸 {size} 无法转换为支持的比例，使用默认值 {DEFAULT_RATIO}")
        return DEFAULT_RATIO

    @retry_on_error(max_retries=5, base_delay=3)
    def generate_image(
        self,
        prompt: str,
        size: str = "1536x864",
        model: str = None,
        reference_image: Optional[bytes] = None,
        reference_images: Optional[List[bytes]] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs
    ) -> bytes:
        """
        生成图片

        Args:
            prompt: 提示词
            size: 图片尺寸 (如 "1536x864", "1024x1024")，会自动转换为比例
            model: 模型名称
            reference_image: 参考图片（向后兼容，bytes类型）
            reference_images: 多张参考图片数据列表（bytes类型）
            reference_image_urls: 参考图片URL列表（新API需要URL）
            **kwargs: 其他参数，支持 ratio, resolution

        Returns:
            图片二进制数据
        """
        if model is None:
            model = self.default_model

        # 获取比例和分辨率参数
        ratio = kwargs.get('ratio') or self._size_to_ratio(size)
        # 验证 ratio 是否支持
        if ratio not in SUPPORTED_RATIOS:
            logger.warning(f"不支持的比例 {ratio}，使用默认值 {DEFAULT_RATIO}")
            ratio = DEFAULT_RATIO
        resolution = kwargs.get('resolution', DEFAULT_RESOLUTION)

        logger.info(f"即梦 API 生成图片: model={model}, ratio={ratio}, resolution={resolution}")

        # 清理提示词
        cleaned_prompt = self._clean_prompt(prompt)

        # 严格限制提示词长度（即梦 API 对长 prompt 敏感）
        if len(cleaned_prompt) > MAX_PROMPT_LENGTH:
            logger.warning(f"提示词过长 ({len(cleaned_prompt)} 字符)，截断至 {MAX_PROMPT_LENGTH} 字符")
            cleaned_prompt = cleaned_prompt[:MAX_PROMPT_LENGTH]

        logger.debug(f"最终 prompt 长度: {len(cleaned_prompt)} 字符")

        # 收集所有参考图片 URL
        all_reference_urls = []
        if reference_image_urls and len(reference_image_urls) > 0:
            all_reference_urls.extend(reference_image_urls)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 根据是否有参考图片选择不同的端点
        if all_reference_urls:
            # 图生图：使用 /v1/images/compositions 端点
            logger.info(f"使用图生图功能，参考图片URL数量: {len(all_reference_urls)}")
            url = f"{self.base_url}/v1/images/compositions"

            payload = {
                "model": model,
                "prompt": cleaned_prompt,
                "images": all_reference_urls,
                "ratio": ratio,
                "resolution": resolution
            }
        else:
            # 文生图：使用 /v1/images/generations 端点
            url = f"{self.base_url}/v1/images/generations"
            payload = {
                "model": model,
                "prompt": cleaned_prompt,
                "negativePrompt": "",
                "ratio": ratio,
                "resolution": resolution
            }

        logger.debug(f"发送请求到 {url}")
        logger.debug(f"请求头: Authorization: Bearer ***")
        logger.debug(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")

        response = requests.post(url, headers=headers, json=payload, timeout=180)

        if response.status_code != 200:
            error_detail = response.text[:500]
            logger.error(f"即梦 API 请求失败: status={response.status_code}, error={error_detail}")
            raise Exception(
                f"即梦 API 请求失败 (状态码: {response.status_code})\n"
                f"错误详情: {error_detail}\n"
                f"请求地址: {url}\n"
                f"模型: {model}\n"
                "可能原因：\n"
                "1. API密钥无效或已过期\n"
                "2. 模型名称不正确或无权访问\n"
                "3. 请求参数不符合要求\n"
                "4. API配额已用尽\n"
                "5. Base URL配置错误\n"
                "建议：检查API密钥、base_url和模型名称配置"
            )

        result = response.json()
        logger.debug(f"  API 响应: {json.dumps(result, ensure_ascii=False)[:500]}")

        # 检查 API 响应体中的错误码（某些代理 API 即使错误也返回 HTTP 200）
        if "code" in result and result["code"] != 0:
            error_code = result.get("code")
            error_message = result.get("message", "未知错误")
            logger.error(f"即梦 API 返回错误: code={error_code}, message={error_message}")
            raise Exception(
                f"即梦 API 错误 (错误码: {error_code})\n"
                f"错误信息: {error_message}\n"
                f"请求地址: {url}\n"
                f"模型: {model}\n"
                "可能原因：\n"
                "1. 请求参数格式不正确\n"
                "2. 提示词过长或包含敏感内容\n"
                "3. API 服务暂时不可用\n"
                "建议：检查提示词内容和长度"
            )

        # 解析即梦API格式的响应
        if "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
            # 获取第一张图片的URL
            first_image = result["data"][0]
            if "url" in first_image:
                image_url = first_image["url"]
                logger.info(f"获取到图片URL: {image_url}")

                # 下载图片
                img_response = requests.get(image_url, timeout=60)
                if img_response.status_code == 200:
                    logger.info(f"✅ 即梦 API 图片生成成功: {len(img_response.content)} bytes")
                    return img_response.content
                else:
                    logger.error(f"下载图片失败: {img_response.status_code}")
                    raise Exception(f"下载图片失败: {img_response.status_code}")

        logger.error(f"API 未返回图片数据: {result}")
        raise ValueError(
            f"即梦 API 未返回图片数据。\n"
            f"响应内容: {result}\n"
            "可能原因：\n"
            "1. 提示词被安全过滤拦截\n"
            "2. 模型不支持图片生成\n"
            "3. 请求格式不正确\n"
            "4. 响应格式解析失败\n"
            "建议：修改提示词或检查模型配置"
        )

    def get_supported_sizes(self) -> list:
        """
        获取支持的图片尺寸

        Returns:
            支持的尺寸列表
        """
        return self.config.get('supported_sizes', ['1536x864', '864x1536', '1024x1024'])
