"""Google GenAI 图片生成器"""
import logging
import time
import random
import base64
from functools import wraps
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from .base import ImageGeneratorBase
from ..utils.image_compressor import compress_image

logger = logging.getLogger(__name__)


def parse_genai_error(error: Exception) -> str:
    """
    解析 Google GenAI API 错误，返回用户友好的错误信息

    识别的错误类型：
    - 401 UNAUTHENTICATED: API Key 无效或认证失败
    - 403 PERMISSION_DENIED: 权限不足
    - 404 NOT_FOUND: 模型不存在
    - 429 RESOURCE_EXHAUSTED: 配额用尽或速率限制
    - 400 INVALID_ARGUMENT: 参数错误
    - 500 INTERNAL: 服务器内部错误
    - 503 UNAVAILABLE: 服务不可用
    - 安全过滤相关错误
    - 网络连接错误
    """
    error_str = str(error).lower()
    error_original = str(error)

    # 401 认证错误
    if "401" in error_str or "unauthenticated" in error_str:
        if "api key" in error_str and "not supported" in error_str:
            return (
                "❌ API Key 认证失败：Vertex AI 不支持 API Key\n\n"
                "【错误原因】\n"
                "您可能误用了 Vertex AI 模式，该模式需要 OAuth2 认证而非 API Key。\n\n"
                "【解决方案】\n"
                "1. 如果您使用 Google AI Studio 的 API Key：\n"
                "   - 确保在设置中没有配置 base_url（留空即可）\n"
                "   - API Key 获取地址: https://aistudio.google.com/app/apikey\n\n"
                "2. 如果您使用 Google Cloud 的 API Key：\n"
                "   - 确保 API Key 已启用 Generative Language API\n"
                "   - 在 Google Cloud Console 检查 API 权限\n\n"
                "3. 如果您确实需要使用 Vertex AI：\n"
                "   - Vertex AI 需要 Service Account 认证，不支持 API Key\n"
                "   - 请参考文档配置 Application Default Credentials"
            )
        else:
            return (
                "❌ API Key 认证失败\n\n"
                "【可能原因】\n"
                "1. API Key 无效或已过期\n"
                "2. API Key 格式错误（复制时可能包含空格）\n"
                "3. API Key 被禁用或删除\n\n"
                "【解决方案】\n"
                "1. 检查 API Key 是否正确复制（无多余空格）\n"
                "2. 前往 Google AI Studio 重新生成 API Key:\n"
                "   https://aistudio.google.com/app/apikey\n"
                "3. 确保 API Key 对应的项目已启用相关 API"
            )

    # 403 权限错误
    if "403" in error_str or "permission_denied" in error_str or "forbidden" in error_str:
        if "billing" in error_str or "quota" in error_str:
            return (
                "❌ 权限被拒绝：计费未启用或配额不足\n\n"
                "【解决方案】\n"
                "1. 检查 Google Cloud 项目是否已启用计费\n"
                "2. 检查 API 配额是否已用尽\n"
                "3. 如果是免费试用账户，可能有使用限制"
            )
        elif "region" in error_str or "location" in error_str:
            return (
                "❌ 权限被拒绝：区域限制\n\n"
                "【解决方案】\n"
                "1. 某些 API 可能在您的地区不可用\n"
                "2. 尝试使用代理或配置 base_url 指向可用区域"
            )
        else:
            return (
                "❌ 权限被拒绝\n\n"
                "【可能原因】\n"
                "1. API Key 没有访问该模型的权限\n"
                "2. 模型可能需要特殊权限或白名单\n"
                "3. 项目配额或限制\n\n"
                "【解决方案】\n"
                "1. 检查 Google Cloud Console 中的 API 权限\n"
                "2. 确认模型是否对您的账户开放\n"
                "3. 尝试使用其他模型（如 gemini-2.0-flash-exp）"
            )

    # 404 资源不存在
    if "404" in error_str or "not_found" in error_str or "not found" in error_str:
        if "model" in error_str:
            return (
                "❌ 模型不存在\n\n"
                "【可能原因】\n"
                "1. 模型名称拼写错误\n"
                "2. 该模型已下线或更名\n"
                "3. 该模型尚未在您的区域开放\n\n"
                "【解决方案】\n"
                "1. 检查模型名称是否正确\n"
                "2. 推荐使用的图片生成模型：\n"
                "   - imagen-3.0-generate-002（推荐）\n"
                "   - gemini-2.0-flash-exp-image-generation\n"
                "3. 查看官方文档获取最新可用模型列表"
            )
        else:
            return (
                "❌ 请求的资源不存在\n\n"
                f"【原始错误】{error_original[:200]}\n\n"
                "【解决方案】检查 API 端点和参数配置"
            )

    # 429 速率限制/配额用尽
    if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
        if "per minute" in error_str or "rpm" in error_str:
            return (
                "⏳ 请求频率超限（RPM 限制）\n\n"
                "【说明】\n"
                "您的请求频率超过了每分钟限制。\n\n"
                "【解决方案】\n"
                "1. 稍等片刻后重试\n"
                "2. 在设置中关闭「高并发模式」\n"
                "3. 减少同时生成的图片数量"
            )
        elif "per day" in error_str or "daily" in error_str:
            return (
                "⏳ 每日配额已用尽\n\n"
                "【说明】\n"
                "您今天的 API 调用次数已达上限。\n\n"
                "【解决方案】\n"
                "1. 等待明天配额重置（通常在 UTC 0:00）\n"
                "2. 升级到付费计划获取更多配额\n"
                "3. 使用其他 API Key"
            )
        else:
            return (
                "⏳ API 配额或速率限制\n\n"
                "【可能原因】\n"
                "1. 请求频率过高\n"
                "2. 免费配额已用尽\n"
                "3. 账户配额达到上限\n\n"
                "【解决方案】\n"
                "1. 稍后再试（通常等待 1-2 分钟）\n"
                "2. 检查 Google Cloud Console 中的配额使用情况\n"
                "3. 考虑升级计划或申请更多配额"
            )

    # 400 参数错误
    if "400" in error_str or "invalid_argument" in error_str or "invalid" in error_str:
        if "image" in error_str and ("size" in error_str or "large" in error_str):
            return (
                "❌ 图片参数错误：图片尺寸过大\n\n"
                "【解决方案】\n"
                "参考图片会自动压缩，但如果仍报错，请尝试上传更小的图片"
            )
        elif "prompt" in error_str or "content" in error_str:
            return (
                "❌ 提示词参数错误\n\n"
                "【可能原因】\n"
                "1. 提示词过长\n"
                "2. 提示词包含不支持的字符\n"
                "3. 提示词触发了内容过滤\n\n"
                "【解决方案】\n"
                "1. 尝试缩短提示词\n"
                "2. 移除特殊字符或敏感内容\n"
                "3. 使用更中性的描述"
            )
        else:
            return (
                f"❌ 请求参数错误\n\n"
                f"【原始错误】{error_original[:300]}\n\n"
                "【解决方案】检查请求参数是否正确"
            )

    # 安全过滤
    if "safety" in error_str or "blocked" in error_str or "filter" in error_str:
        return (
            "🛡️ 内容被安全过滤器拦截\n\n"
            "【说明】\n"
            "您的提示词或生成内容触发了 Google 的安全过滤机制。\n\n"
            "【解决方案】\n"
            "1. 修改提示词，使用更中性的描述\n"
            "2. 避免涉及敏感话题的内容\n"
            "3. 尝试换一种表达方式描述相同内容"
        )

    # 图片生成特定错误
    if "could not generate" in error_str or "unable to generate" in error_str:
        return (
            "❌ 模型无法生成图片\n\n"
            "【可能原因】\n"
            "1. 该模型不支持图片生成功能\n"
            "2. 提示词过于复杂或模糊\n"
            "3. 模型暂时不可用\n\n"
            "【解决方案】\n"
            "1. 确认使用支持图片生成的模型：\n"
            "   - imagen-3.0-generate-002\n"
            "   - gemini-2.0-flash-exp-image-generation\n"
            "2. 简化提示词描述\n"
            "3. 稍后再试"
        )

    # 500 服务器错误
    if "500" in error_str or "internal" in error_str:
        return (
            "⚠️ Google API 服务器内部错误\n\n"
            "【说明】\n"
            "这是 Google 服务端的临时故障，与您的配置无关。\n\n"
            "【解决方案】\n"
            "1. 稍等几分钟后重试\n"
            "2. 如果持续出现，可检查 Google Cloud Status"
        )

    # 503 服务不可用
    if "503" in error_str or "unavailable" in error_str:
        return (
            "⚠️ Google API 服务暂时不可用\n\n"
            "【说明】\n"
            "服务正在维护或临时过载。\n\n"
            "【解决方案】\n"
            "1. 稍等几分钟后重试\n"
            "2. 检查 Google Cloud Status 了解服务状态"
        )

    # 网络错误
    if "timeout" in error_str or "timed out" in error_str:
        return (
            "⏱️ 请求超时\n\n"
            "【可能原因】\n"
            "1. 网络连接不稳定\n"
            "2. API 服务响应缓慢\n"
            "3. 图片生成耗时过长\n\n"
            "【解决方案】\n"
            "1. 检查网络连接\n"
            "2. 重试请求\n"
            "3. 如果使用代理，检查代理是否正常"
        )

    if "connection" in error_str or "network" in error_str or "refused" in error_str:
        return (
            "🌐 网络连接错误\n\n"
            "【可能原因】\n"
            "1. 网络连接中断\n"
            "2. 无法访问 Google API（可能被防火墙阻止）\n"
            "3. 代理配置问题\n\n"
            "【解决方案】\n"
            "1. 检查网络连接是否正常\n"
            "2. 如果在中国大陆，可能需要配置代理\n"
            "3. 在设置中配置 base_url 指向可用的代理地址"
        )

    if "ssl" in error_str or "certificate" in error_str:
        return (
            "🔒 SSL/TLS 证书错误\n\n"
            "【可能原因】\n"
            "1. 系统时间不正确\n"
            "2. 代理或防火墙干扰 HTTPS 连接\n"
            "3. 证书过期或无效\n\n"
            "【解决方案】\n"
            "1. 检查系统时间是否正确\n"
            "2. 检查代理或防火墙设置"
        )

    # 默认错误
    return (
        f"❌ API 调用失败\n\n"
        f"【原始错误】\n{error_original[:500]}\n\n"
        "【通用解决方案】\n"
        "1. 检查 API Key 是否正确配置\n"
        "2. 检查网络连接是否正常\n"
        "3. 尝试更换模型或简化提示词\n"
        "4. 查看后端日志获取更多信息"
    )


def retry_on_error(max_retries=5, base_delay=3):
    """智能重试装饰器，根据错误类型决定是否重试"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()

                    # 不可重试的错误类型
                    non_retryable = [
                        "401", "unauthenticated",  # 认证错误
                        "403", "permission_denied", "forbidden",  # 权限错误
                        "404", "not_found",  # 资源不存在
                        "invalid_argument",  # 参数错误
                        "safety", "blocked", "filter",  # 安全过滤
                    ]

                    should_retry = True
                    for keyword in non_retryable:
                        if keyword in error_str:
                            should_retry = False
                            break

                    if not should_retry:
                        # 直接抛出，不重试
                        raise Exception(parse_genai_error(e))

                    # 可重试的错误
                    if attempt < max_retries - 1:
                        if "429" in error_str or "resource_exhausted" in error_str:
                            wait_time = (base_delay ** attempt) + random.uniform(0, 1)
                            logger.warning(f"⏳ 遇到速率限制，{wait_time:.1f}秒后重试 (尝试 {attempt + 2}/{max_retries})")
                        else:
                            wait_time = min(2 ** attempt, 10) + random.uniform(0, 1)
                            logger.warning(f"⚠️ 请求失败，{wait_time:.1f}秒后重试 (尝试 {attempt + 2}/{max_retries})")
                        time.sleep(wait_time)
                        continue

                    # 重试次数耗尽
                    raise Exception(parse_genai_error(e))

            # 理论上不会到这里，但保险起见
            raise Exception(parse_genai_error(last_error))
        return wrapper
    return decorator


class GoogleGenAIGenerator(ImageGeneratorBase):
    """Google GenAI 图片生成器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        logger.debug("初始化 GoogleGenAIGenerator...")

        if not self.api_key:
            logger.error("Google GenAI API Key 未配置")
            raise ValueError(
                "Google GenAI API Key 未配置。\n"
                "解决方案：在系统设置页面编辑该服务商，填写 API Key\n"
                "获取 API Key: https://aistudio.google.com/app/apikey"
            )

        # 初始化客户端
        logger.debug("初始化 Google GenAI 客户端...")
        client_kwargs = {
            "api_key": self.api_key,
        }

        # 默认使用 Gemini API (vertexai=False)，因为大多数用户使用 Google AI Studio 的 API Key
        # Vertex AI 需要 OAuth2 认证，不支持 API Key
        self.is_vertexai = False

        # 如果有 base_url，则配置 http_options
        if self.config.get('base_url'):
            logger.debug(f"  使用自定义 base_url: {self.config['base_url']}")
            client_kwargs["http_options"] = {
                "base_url": self.config['base_url'],
                "api_version": "v1beta"
            }

        client_kwargs["vertexai"] = False

        self.client = genai.Client(**client_kwargs)

        # 默认安全设置
        self.safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ]
        logger.info("GoogleGenAIGenerator 初始化完成")

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.api_key)

    @retry_on_error(max_retries=5, base_delay=3)
    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "3:4",
        temperature: float = 1.0,
        model: str = "gemini-3-pro-image-preview",
        reference_image: Optional[bytes] = None,
        **kwargs
    ) -> bytes:
        """
        生成图片

        Args:
            prompt: 提示词
            aspect_ratio: 宽高比 (如 "3:4", "1:1", "16:9")
            temperature: 温度
            model: 模型名称
            reference_image: 参考图片二进制数据（用于保持风格一致）
            **kwargs: 其他参数

        Returns:
            图片二进制数据
        """
        logger.info(f"Google GenAI 生成图片: model={model}, aspect_ratio={aspect_ratio}")
        logger.debug(f"  prompt 长度: {len(prompt)} 字符, 有参考图: {reference_image is not None}")

        # 构建 parts 列表
        parts = []

        # 如果有参考图，先添加参考图和说明
        if reference_image:
            logger.debug(f"  添加参考图片 ({len(reference_image)} bytes)")
            # 压缩参考图到 200KB 以内
            compressed_ref = compress_image(reference_image, max_size_kb=200)
            logger.debug(f"  参考图压缩后: {len(compressed_ref)} bytes")
            # 添加参考图
            parts.append(types.Part(
                inline_data=types.Blob(
                    mime_type="image/png",
                    data=compressed_ref
                )
            ))
            # 添加带参考说明的提示词
            enhanced_prompt = f"""请参考上面这张图片的视觉风格（包括配色、排版风格、字体风格、装饰元素风格），生成一张风格一致的新图片。

新图片的内容要求：
{prompt}

重要：
1. 必须保持与参考图相同的视觉风格和设计语言
2. 配色方案要与参考图协调一致
3. 排版和装饰元素的风格要统一
4. 但内容要按照新的要求来生成"""
            parts.append(types.Part(text=enhanced_prompt))
        else:
            # 没有参考图，直接使用原始提示词
            parts.append(types.Part(text=prompt))

        contents = [
            types.Content(
                role="user",
                parts=parts
            )
        ]

        image_config_kwargs = {
            "aspect_ratio": aspect_ratio,
        }

        # 只有在 Vertex AI 模式下才支持 output_mime_type
        if self.is_vertexai:
            image_config_kwargs["output_mime_type"] = "image/png"

        generate_content_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            max_output_tokens=32768,
            response_modalities=["TEXT", "IMAGE"],
            safety_settings=self.safety_settings,
            image_config=types.ImageConfig(**image_config_kwargs),
        )

        image_data = None
        logger.debug(f"  开始调用 API: model={model}")
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    # 检查是否有图片数据
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        logger.debug(f"  收到图片数据: {len(image_data)} bytes")
                        break

        if not image_data:
            logger.error("API 返回为空，未生成图片")
            raise ValueError(
                "❌ 图片生成失败：API 返回为空\n\n"
                "【可能原因】\n"
                "1. 提示词触发了安全过滤（最常见）\n"
                "2. 模型不支持当前的图片生成请求\n"
                "3. 网络传输过程中数据丢失\n\n"
                "【解决方案】\n"
                "1. 修改提示词，避免敏感内容：\n"
                "   - 避免涉及暴力、血腥、色情等内容\n"
                "   - 避免涉及真实人物（明星、政治人物等）\n"
                "   - 使用更中性、积极的描述\n"
                "2. 尝试简化提示词\n"
                "3. 检查网络连接后重试"
            )

        logger.info(f"✅ Google GenAI 图片生成成功: {len(image_data)} bytes")
        return image_data

    def get_supported_aspect_ratios(self) -> list:
        """获取支持的宽高比"""
        return ["1:1", "3:4", "4:3", "16:9", "9:16"]
