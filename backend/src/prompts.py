"""Prompt templates for AI polishing."""

from typing import Optional
import yaml
import json
from pathlib import Path

from .chunking import Chunk, get_chunk_context


# System prompt for Vietnamese novel polishing (co trang style)
SYSTEM_PROMPT_POLISH_VI = """Bạn là biên tập viên chuyên nghiệp cho tiểu thuyết cổ trang Trung Hoa chuyển ngữ tiếng Việt.
Phong cách mục tiêu: nhẹ nhàng, hài đời thường, như truyện "Tiêu Dao Tiểu Thư Sinh" (逍遥小书生).

NHIỆM VỤ:
- Biên tập lại đoạn văn cho mượt mà, tự nhiên, dễ đọc
- GIỮ NGUYÊN nội dung, ý nghĩa, tình tiết - KHÔNG thêm/bớt/tóm tắt/bình luận
- Sửa câu lủng củng, lặp từ, dịch sát máy móc
- Giữ nhịp hài nhẹ - không giải thích trò đùa, chỉ làm punchline rõ hơn
- Thống nhất xưng hô và tước vị theo STYLE và GLOSSARY được cung cấp

QUY TẮC NGÔN NGỮ:
- Văn phong cổ trang ĐỜI THƯỜNG, không khoa trương kiếm hiệp
- TRÁNH slang hiện đại: ok, deadline, trend, drama, vibe, toxic, slay...
- Giữ cách gọi: "công tử", "cô nương", "lão gia" - tránh "anh/em" quá hiện đại trừ khi phù hợp
- Câu gọn, nhịp nhàng, không rườm rà
- Dấu câu chuẩn: "…" cho ngoặc kép, … cho dấu ba chấm

OUTPUT: Chỉ trả về văn bản đã biên tập, KHÔNG có lời giải thích hay bình luận."""

# System prompt for English translation
SYSTEM_PROMPT_TRANSLATE_EN = """You are a professional translator specializing in Chinese web novels.
Target style: Light, humorous slice-of-life like "Mo Dao Zu Shi" or "Heaven Official's Blessing".

TASK:
- Translate the Vietnamese text to natural, flowing English
- Keep the original meaning, plot, and tone intact
- Maintain the light comedic timing - don't explain jokes
- Use consistent terms as specified in GLOSSARY

LANGUAGE RULES:
- Natural English prose, not stilted translation
- Keep honorifics where appropriate (Young Master, Miss, Lord)
- Avoid overly modern slang
- Maintain paragraph structure

OUTPUT: Only return the translated text, no explanations or comments."""


def load_style_file(style_path: Optional[Path]) -> str:
    """Load style configuration as YAML string."""
    if style_path and style_path.exists():
        with open(style_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def load_glossary_file(glossary_path: Optional[Path]) -> str:
    """Load glossary as JSON string."""
    if glossary_path and glossary_path.exists():
        with open(glossary_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "{}"


def get_system_prompt(mode: str) -> str:
    """Get appropriate system prompt for the mode."""
    if mode == "polish_vi":
        return SYSTEM_PROMPT_POLISH_VI
    elif mode == "translate_en":
        return SYSTEM_PROMPT_TRANSLATE_EN
    else:
        return SYSTEM_PROMPT_POLISH_VI


def build_user_prompt(
    chunk: Chunk,
    style_content: str = "",
    glossary_content: str = ""
) -> str:
    """
    Build the user prompt for a chunk.
    
    Args:
        chunk: The text chunk to process
        style_content: YAML style configuration content
        glossary_content: JSON glossary content
        
    Returns:
        Formatted prompt string
    """
    context = get_chunk_context(chunk)
    
    parts = [f"## {context}\n"]
    
    if style_content:
        parts.append("### STYLE GUIDE:")
        parts.append("```yaml")
        parts.append(style_content.strip())
        parts.append("```\n")
    
    if glossary_content and glossary_content != "{}":
        parts.append("### GLOSSARY:")
        parts.append("```json")
        parts.append(glossary_content.strip())
        parts.append("```\n")
    
    parts.append("### TEXT TO EDIT:")
    parts.append(chunk.text)
    
    return "\n".join(parts)
