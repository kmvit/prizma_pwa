"""
Сервис генерации PDF-отчётов. Адаптирован из perplexy_bot для PWA (user.id вместо telegram_id).
"""
import re
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from io import BytesIO

from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color

from app.database.models import User

# Пути относительно backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class PDFGenerator:
    """Генератор PDF страниц с текстом"""

    def __init__(self):
        self.template_dir = BASE_DIR / "template_pdf"
        self.fonts_dir = BASE_DIR / "fonts"
        self.fallback_fonts_dir = BASE_DIR.parent / "frontend" / "public" / "fonts"
        self._setup_fonts()

    def clean_markdown_text(self, text: str) -> str:
        """Очистка текста от markdown разметки и форматирование для PDF"""
        if not text or not text.strip():
            return ""
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'^#####\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)
        text = re.sub(r'^####\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)
        text = re.sub(r'^###\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)
        text = re.sub(r'^##\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)
        text = re.sub(r'^#\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'^[-=_]{3,}\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'[`~]', '', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'^-\s+(.+)$', r'• \1', text, flags=re.MULTILINE)
        lines = text.split('\n')
        processed_lines = []
        for line in lines:
            if re.match(r'^\d+\.\s+(.+)$', line):
                processed_lines.append(line if len(line.strip()) < 80 else re.sub(r'^\d+\.\s+(.+)$', r'\1', line))
            else:
                processed_lines.append(line)
        text = '\n'.join(processed_lines)
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def _process_markdown_tables(self, text: str) -> str:
        """Обработка markdown таблиц"""
        lines = text.split('\n')
        processed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if '|' in line and line.count('|') >= 2:
                while i < len(lines) and ('|' in lines[i] or not lines[i].strip()):
                    if lines[i].strip():
                        processed_lines.append(lines[i].strip())
                    i += 1
            else:
                processed_lines.append(line)
                i += 1
        return '\n'.join(processed_lines)

    def _setup_fonts(self):
        """Настройка шрифтов для русского текста"""
        try:
            opensans_path = self.fallback_fonts_dir / "OpenSans-Regular.ttf"
            montserrat_path = self.fallback_fonts_dir / "Montserrat-Regular.ttf"
            if opensans_path.exists():
                pdfmetrics.registerFont(TTFont('OpenSans', str(opensans_path)))
                self.default_font = 'OpenSans'
            elif montserrat_path.exists():
                pdfmetrics.registerFont(TTFont('Montserrat', str(montserrat_path)))
                self.default_font = 'Montserrat'
            else:
                self.default_font = 'Helvetica'
            self.bold_font = self.default_font
        except Exception:
            self.default_font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'

    def _wrap_line(self, text_canvas, text, font_name, font_size, max_width):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        if stringWidth(text, font_name, font_size) <= max_width:
            return [text]
        words = text.split(' ')
        lines = []
        current = ''
        for word in words:
            test = (current + ' ' + word).strip() if current else word
            if stringWidth(test, font_name, font_size) > max_width:
                if current:
                    lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    def create_text_pages(self, text: str, template_path: Path, page_width: float = A4[0], page_height: float = A4[1]) -> list:
        """Создание PDF страниц с текстом на основе шаблона"""
        if not template_path.exists():
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")
        text = self.clean_markdown_text(text)
        if not text or not text.strip():
            return []
        lines = [l for l in text.strip().split('\n') if l.strip()]
        if not lines:
            return []
        left_margin, right_margin = 75, 75
        top_margin, bottom_margin = 100, 100
        text_width = page_width - left_margin - right_margin
        text_height = page_height - top_margin - bottom_margin
        line_height, h1_height, h2_height = 14, 24, 18
        main_color = Color(1/255, 28/255, 92/255)
        h1_color = Color(218/255, 5/255, 52/255)
        h2_color = Color(2/255, 88/255, 185/255)
        h1_keywords = ['как вы мыслите', 'кто вы по типу', 'какие паттерны', 'как вы воспринимаете']
        h2_keywords = ['подкрепляющая цитата', 'практические рекомендации', 'техники работы']
        pages, current_lines, current_height = [], [], 0
        for line in lines:
            l = line.strip()
            kind = 'text'
            h = line_height
            if len(l) < 120 and any(k in l.lower() for k in h1_keywords):
                kind, h = 'h1', h1_height
            elif any(k in l.lower() for k in h2_keywords) or (l.endswith(':') and len(l) < 100):
                kind, h = 'h2', h2_height
            wrapped = self._wrap_line(None, l, self.bold_font if kind != 'text' else self.default_font, 18 if kind == 'h1' else 14 if kind == 'h2' else 11, text_width)
            for wline in wrapped:
                wh = h1_height if kind == 'h1' else h2_height if kind == 'h2' else line_height
                if current_height + wh > text_height - 50 and current_lines:
                    pages.append(current_lines)
                    current_lines, current_height = [], 0
                current_lines.append((wline, kind, 'h1' if kind == 'h1' else 'h2' if kind == 'h2' else None))
                current_height += wh
        if current_lines:
            pages.append(current_lines)
        result_buffers = []
        for page_lines in pages:
            text_buffer = BytesIO()
            text_canvas = canvas.Canvas(text_buffer, pagesize=A4)
            text_canvas.setFont(self.default_font, 11)
            text_canvas.setFillColor(main_color)
            y_position = page_height - top_margin
            for line, kind, _ in page_lines:
                l = line.strip()
                if kind == 'h1':
                    y_position -= 10
                    text_canvas.setFont(self.bold_font, 18)
                    text_canvas.setFillColor(h1_color)
                    text_canvas.drawString(left_margin, y_position, l)
                    y_position -= h1_height
                elif kind == 'h2':
                    y_position -= 8
                    text_canvas.setFont(self.default_font, 14)
                    text_canvas.setFillColor(h2_color)
                    text_canvas.drawString(left_margin, y_position, l)
                    y_position -= h2_height
                else:
                    text_canvas.setFont(self.default_font, 11)
                    text_canvas.setFillColor(main_color)
                    text_canvas.drawString(left_margin, y_position, l)
                    y_position -= line_height
                text_canvas.setFont(self.default_font, 11)
                text_canvas.setFillColor(main_color)
            text_canvas.save()
            text_buffer.seek(0)
            template_reader = PdfReader(str(template_path))
            template_page = template_reader.pages[0]
            text_reader = PdfReader(text_buffer)
            text_page = text_reader.pages[0]
            template_page.merge_page(text_page)
            result_buffer = BytesIO()
            writer = PdfWriter()
            writer.add_page(template_page)
            writer.write(result_buffer)
            result_buffer.seek(0)
            result_buffers.append(result_buffer)
        return result_buffers

    def combine_pdfs(self, pdf_parts: List[Path], output_path: Path) -> bool:
        """Объединение PDF файлов в один"""
        try:
            writer = PdfWriter()
            for pdf_path in pdf_parts:
                if pdf_path.exists():
                    reader = PdfReader(str(pdf_path))
                    for page in reader.pages:
                        writer.add_page(page)
                else:
                    return False
            with open(output_path, 'wb') as f:
                writer.write(f)
            return True
        except Exception:
            return False

    def create_custom_title_page(self, template_path: Path, user_name: str, completion_date: str) -> BytesIO:
        """Создание титульной страницы с данными пользователя"""
        if not template_path.exists():
            raise FileNotFoundError(f"Шаблон титульной страницы не найден: {template_path}")
        user_info_text = f"Создано для {user_name}\n{completion_date}"
        text_buffer = BytesIO()
        text_canvas = canvas.Canvas(text_buffer, pagesize=A4)
        text_canvas.setFont(self.default_font, 12)
        main_color = Color(1/255, 28/255, 92/255)
        page_width, page_height = A4
        x_position = page_width / 2
        y_position = (page_height / 2) - 200
        text_canvas.setFillColor(main_color)
        text_canvas.setFont(self.default_font, 16)
        from reportlab.pdfbase.pdfmetrics import stringWidth
        for line in user_info_text.split('\n'):
            text_width = stringWidth(line, self.default_font, 16)
            centered_x = x_position - (text_width / 2)
            text_canvas.drawString(centered_x, y_position, line)
            y_position -= 25
        text_canvas.save()
        text_buffer.seek(0)
        template_reader = PdfReader(str(template_path))
        template_page = template_reader.pages[0]
        text_reader = PdfReader(text_buffer)
        text_page = text_reader.pages[0]
        template_page.merge_page(text_page)
        result_buffer = BytesIO()
        writer = PdfWriter()
        writer.add_page(template_page)
        writer.write(result_buffer)
        result_buffer.seek(0)
        return result_buffer


class ReportGenerator:
    """Генератор PDF отчетов (PWA: user.id вместо telegram_id)"""

    def __init__(self):
        self.reports_dir = BASE_DIR / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.template_dir = BASE_DIR / "template_pdf"
        self.template_premium_dir = BASE_DIR / "template_pdf_premium"
        self.pdf_generator = PDFGenerator()

    def _user_id(self, user: User) -> int:
        return getattr(user, 'id', None) or getattr(user, 'telegram_id', 0)

    def create_text_report(self, user: User, analysis_result: Dict) -> str:
        """Текстовый отчет (fallback)"""
        uid = self._user_id(user)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.reports_dir / f"prizma_report_{uid}_{ts}.txt"
        page3 = self.pdf_generator.clean_markdown_text(analysis_result.get('page3_analysis', 'Анализ не доступен'))
        page4 = self.pdf_generator.clean_markdown_text(analysis_result.get('page4_analysis', 'Анализ не доступен'))
        page5 = self.pdf_generator.clean_markdown_text(analysis_result.get('page5_analysis', 'Анализ не доступен'))
        content = f"СТРАНИЦА 3: КТО ВЫ ПО ТИПУ ЛИЧНОСТИ?\n{'='*60}\n{page3}\n\nСТРАНИЦА 4: КАК ВЫ МЫСЛИТЕ?\n{'='*60}\n{page4}\n\nСТРАНИЦА 5: ПАТТЕРНЫ\n{'='*60}\n{page5}"
        filepath.write_text(content, encoding='utf-8')
        return str(filepath)

    def create_pdf_report(self, user: User, analysis_result: Dict) -> str:
        """Создание полного PDF отчета (страницы 3, 4, 5)"""
        uid = self._user_id(user)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = self.reports_dir / f"prizma_report_{uid}_{ts}.pdf"
        try:
            temp_dir = self.reports_dir / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_files = []
            for key, tpl in [('page3_analysis', "3.pdf"), ('page4_analysis', "4.pdf"), ('page5_analysis', "5.pdf")]:
                if analysis_result.get(key):
                    tpath = self.template_dir / tpl
                    buffers = self.pdf_generator.create_text_pages(analysis_result[key], tpath)
                    for i, buf in enumerate(buffers):
                        page_path = temp_dir / f"page_{key}_{i+1}.pdf"
                        page_path.write_bytes(buf.getvalue())
                        temp_files.append(page_path)
            pdf_parts = [self.template_dir / "1.pdf", self.template_dir / "2.pdf"]
            pdf_parts.extend(temp_files)
            pdf_parts.extend([self.template_dir / "6.pdf", self.template_dir / "7.pdf"])
            success = self.pdf_generator.combine_pdfs(pdf_parts, output_path)
            for f in temp_files:
                if f.exists():
                    f.unlink()
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
            if success:
                return str(output_path)
            raise Exception("Ошибка объединения PDF")
        except Exception:
            return self.create_text_report(user, analysis_result)

    def create_free_basic_pdf_report(self, user: User, analysis_result: Dict) -> str:
        """Упрощенный бесплатный PDF (personality_type, uniqueness, key_insight)"""
        uid = self._user_id(user)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = self.reports_dir / f"prizma_report_{uid}_{ts}.pdf"
        try:
            temp_dir = self.reports_dir / "temp_free"
            temp_dir.mkdir(exist_ok=True)
            temp_files = []
            t3 = self.template_dir / "3.pdf"
            t4 = self.template_dir / "4.pdf"
            t5 = self.template_dir / "5.pdf"
            for key, tpl in [('personality_type', t3), ('uniqueness', t4), ('key_insight', t5)]:
                if analysis_result.get(key):
                    for i, buf in enumerate(self.pdf_generator.create_text_pages(analysis_result[key], tpl)):
                        p = temp_dir / f"{key}_{i+1}.pdf"
                        p.write_bytes(buf.getvalue())
                        temp_files.append(p)
            pdf_parts = [self.template_dir / "1.pdf"]
            pdf_parts.extend(temp_files)
            pdf_parts.extend([self.template_dir / "6.pdf", self.template_dir / "7.pdf"])
            success = self.pdf_generator.combine_pdfs(pdf_parts, output_path)
            for f in temp_files:
                if f.exists():
                    f.unlink()
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
            if success:
                return str(output_path)
            raise Exception("Ошибка объединения PDF")
        except Exception:
            return self.create_text_report(user, analysis_result)

    def _get_premium_block_template_mapping(self):
        return {
            "premium_analysis": "block-1", "premium_strengths": "block-2",
            "premium_growth_zones": "block-3", "premium_compensation": "block-4",
            "premium_interaction": "block-5", "premium_prognosis": "block-6",
            "premium_practical": "block-7", "premium_conclusion": "block-8",
            "premium_appendix": "block-9",
        }

    def _generate_premium_pdf_by_blocks(self, individual_pages: dict, temp_dir: Path, temp_files: list, user: User) -> list:
        pdf_parts = []
        premium_templates_dir = self.template_premium_dir
        ai_template_path = self.template_dir / "3.pdf"
        block_mapping = self._get_premium_block_template_mapping()
        pages_by_section = {}
        for page_key, page_data in individual_pages.items():
            section_key = page_data["section_key"]
            if section_key not in pages_by_section:
                pages_by_section[section_key] = []
            pages_by_section[section_key].append((page_key, page_data))
        ordered_sections = ["premium_analysis", "premium_strengths", "premium_growth_zones", "premium_compensation",
            "premium_interaction", "premium_prognosis", "premium_practical", "premium_conclusion", "premium_appendix"]
        block1_dir = premium_templates_dir / "block-1"
        title_pdf = block1_dir / "title.pdf"
        title2_pdf = block1_dir / "title-2.pdf"
        user_name = user.name or f"пользователя {self._user_id(user)}"
        completion_date = datetime.utcnow().strftime("%d.%m.%Y")
        if title_pdf.exists():
            buf = self.pdf_generator.create_custom_title_page(title_pdf, user_name, completion_date)
            p = temp_dir / "custom_title.pdf"
            p.write_bytes(buf.getvalue())
            temp_files.append(p)
            pdf_parts.append(p)
        if title2_pdf.exists():
            pdf_parts.append(title2_pdf)
        for section_key in ordered_sections:
            if section_key not in pages_by_section:
                continue
            block_folder = block_mapping.get(section_key)
            block_templates_dir = premium_templates_dir / block_folder
            if not block_templates_dir.exists():
                continue
            section_pages = sorted(pages_by_section[section_key], key=lambda x: x[1]["page_num"])
            block_title = block_templates_dir / "1.pdf"
            if block_title.exists():
                pdf_parts.append(block_title)
            for i, (_, page_data) in enumerate(section_pages, start=1):
                content = page_data.get("content", "")
                global_page = page_data["global_page"]
                static_pdf = block_templates_dir / f"{i + 1}.pdf"
                if static_pdf.exists():
                    pdf_parts.append(static_pdf)
                if content and content.strip():
                    for idx, buf in enumerate(self.pdf_generator.create_text_pages(content, ai_template_path)):
                        if buf and buf.getvalue():
                            ap = temp_dir / f"ai_{global_page:02d}_{idx+1}.pdf"
                            ap.write_bytes(buf.getvalue())
                            temp_files.append(ap)
                            pdf_parts.append(ap)
            note_pdf = block_templates_dir / "note.pdf"
            if note_pdf.exists():
                pdf_parts.append(note_pdf)
        last_pdf = premium_templates_dir / "block-9" / "last.pdf"
        if last_pdf.exists():
            pdf_parts.append(last_pdf)
        return pdf_parts

    def create_premium_pdf_report(self, user: User, analysis_result: Dict) -> str:
        uid = self._user_id(user)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = self.reports_dir / f"prizma_premium_report_{uid}_{ts}.pdf"
        try:
            temp_dir = self.reports_dir / "temp_premium"
            temp_dir.mkdir(exist_ok=True)
            temp_files = []
            individual_pages = analysis_result.get("individual_pages", {})
            if individual_pages:
                pdf_parts = self._generate_premium_pdf_by_blocks(individual_pages, temp_dir, temp_files, user)
            else:
                blocks = ["premium_analysis", "premium_compensation", "premium_prognosis", "premium_practical", "premium_conclusion", "premium_appendix"]
                tpl = self.template_dir / "3.pdf"
                for key in blocks:
                    if analysis_result.get(key):
                        for i, buf in enumerate(self.pdf_generator.create_text_pages(analysis_result[key], tpl)):
                            p = temp_dir / f"{key}_{i+1}.pdf"
                            p.write_bytes(buf.getvalue())
                            temp_files.append(p)
                pdf_parts = ([self.template_dir / "1.pdf"] if (self.template_dir / "1.pdf").exists() else [])
                for key in blocks:
                    for p in sorted(temp_dir.glob(f"{key}_*.pdf"), key=lambda x: int(x.stem.rsplit("_", 1)[-1]) if x.stem.rsplit("_", 1)[-1].isdigit() else 0):
                        pdf_parts.append(p)
                if (self.template_dir / "6.pdf").exists():
                    pdf_parts.append(self.template_dir / "6.pdf")
                if (self.template_dir / "7.pdf").exists():
                    pdf_parts.append(self.template_dir / "7.pdf")
            success = self.pdf_generator.combine_pdfs(pdf_parts, output_path)
            for f in temp_files:
                if f.exists():
                    f.unlink()
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
            if success:
                return str(output_path)
            raise Exception("Ошибка объединения PDF")
        except Exception:
            return self.create_premium_text_report(user, analysis_result)

    def create_premium_text_report(self, user: User, analysis_result: Dict) -> str:
        uid = self._user_id(user)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fp = self.reports_dir / f"prizma_premium_report_{uid}_{ts}.txt"
        section_keys = ["premium_analysis", "premium_strengths", "premium_growth_zones", "premium_compensation",
            "premium_interaction", "premium_prognosis", "premium_practical", "premium_conclusion", "premium_appendix"]
        parts = [self.pdf_generator.clean_markdown_text(analysis_result[k]) for k in section_keys if analysis_result.get(k)]
        fp.write_text("\n\n".join(parts) if parts else "Отчёт не доступен", encoding="utf-8")
        return str(fp)
