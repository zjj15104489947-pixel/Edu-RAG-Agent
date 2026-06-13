"""langchain封装版文本切分工具，将长课程资料切成适合检索和向量化的小文本块。"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

# ============ 进行PDF页级文本的chunk划分 ===========

def pages_to_documents(pages: list[dict]) -> list[Document]:
    """Convert PDF page dictionaries into LangChain Document objects."""

    documents = []

    for page_data in pages:
        text = page_data["text"]
        source = page_data["source"]
        page = page_data["page"]

        if not text.strip():
            continue

        documents.append(

            # 创建 Document 对象
            Document(
                page_content=text,
                metadata={
                    "source": source,
                    "page": page,
                },
            )
        )

    return documents

# 公用的切割器
def shared_split_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[Document]:
    """Split LangChain Documents into smaller chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap 不能小于 0")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")
    
    # 创建一个文本切分器对象
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # 调用 Langchain 内部函数进行切割
    return splitter.split_documents(documents)

def chunk_pdf_pages_with_langchain(
        pages: list[dict],
        chunk_size: int = 800,
        chunk_overlap: int = 100,
) -> list[Document]:
    """Convert PDF pages to Documents and split them into chunks."""

    documents = pages_to_documents(pages)

    return shared_split_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

# ============ 进行Markdown文本的chunk划分 ===========

def parse_markdown_sections(markdown_text: str, source: str) -> list[Document]:
    """Parse Markdown text into section-level LangChain Documents."""

    if not markdown_text.strip():
        raise ValueError("Markdown 文本为空，无法切分")

    heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

    sections = []                    # 最终装所有章节 Document 的容器
    current_title = None             # 当前正在收集的章节标题
    current_level = None             # 当前标题级别（1-6）
    current_lines = []               # 当前章节的内容行（字符串列表）
    heading_stack: list[tuple[int, str]] = []   # 标题层级栈

# 把"当前正在收集的内容"打包成一个 Document，塞进 sections 列表。
    def flush_current_section() -> None:
        """Save the current section as a Document if it has content."""

        if current_title is None:
            content = "\n".join(current_lines).strip()
            if content:
                sections.append(
                    Document(
                        page_content=content,
                        metadata={
                            "source": source,
                            "file_type": "markdown",
                            "section_title": "Document Start",
                            "header_level": 0,
                            "header_path": "Document Start",
                        },
                    )
                )
            return

        content = "\n".join(current_lines).strip()
        if not content:
            return

        header_path = " > ".join(title for _, title in heading_stack)

        sections.append(
            Document(
                page_content=f"{current_title}\n\n{content}",
                metadata={
                    "source": source,
                    "file_type": "markdown",
                    "section_title": current_title,
                    "header_level": current_level,
                    "header_path": header_path,
                },
            )
        )
    
    for line in markdown_text.splitlines():
        match = heading_pattern.match(line)

        if match:
            flush_current_section()

            hashes, title = match.groups()
            level = len(hashes)
            title = title.strip()

            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()

            heading_stack.append((level, title))

            current_title = title
            current_level = level
            current_lines = []
        else:
            current_lines.append(line)

    flush_current_section()

    if sections:
        return sections

    return [
        Document(
            page_content=markdown_text.strip(),
            metadata={
                "source": source,
                "file_type": "markdown",
                "section_title": "Full Document",
                "header_level": 0,
                "header_path": "Full Document",
            },
        )
    ]

def chunk_markdown_text_with_langchain(
    markdown_text: str,
    source: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[Document]:
    """Parse Markdown into section Documents and split them into chunks."""

    section_documents = parse_markdown_sections(
        markdown_text=markdown_text,
        source=source,
    )

    return shared_split_documents(
        section_documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )