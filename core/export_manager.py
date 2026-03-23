"""
Export Manager - Export translations and data in various formats

Provides export functionality for:
- Translation history
- Session transcripts
- Video with subtitles
- PDF reports
"""
import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ExportFormat(Enum):
    """Supported export formats."""
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
    SRT = "srt"      # Subtitles
    HTML = "html"


@dataclass
class ExportConfig:
    """Export configuration options."""
    format: ExportFormat = ExportFormat.TXT
    include_timestamps: bool = True
    include_confidence: bool = False
    include_gesture_types: bool = False
    date_format: str = "%Y-%m-%d %H:%M:%S"
    output_dir: str = ""


@dataclass
class TranslationRecord:
    """A translation record for export."""
    text: str
    timestamp: datetime
    confidence: float = 0.0
    gesture_type: str = "static"
    duration: float = 0.0


class ExportManager:
    """Manages export of translations and session data.
    
    Features:
    - Multiple format support (TXT, CSV, JSON, PDF, SRT)
    - Customizable export options
    - Subtitle generation for videos
    - Share to clipboard functionality
    """
    
    def __init__(self, output_dir: str = None):
        self.config = ExportConfig()
        if output_dir:
            self.config.output_dir = output_dir
        else:
            # Default to user's documents folder
            self.config.output_dir = os.path.join(
                os.path.expanduser("~"), "Documents", "SignLanguage_Exports"
            )
        
        os.makedirs(self.config.output_dir, exist_ok=True)
    
    def _generate_filename(self, prefix: str, format: ExportFormat) -> str:
        """Generate a unique filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{format.value}"
    
    def export_translations(self, translations: List[TranslationRecord],
                           format: ExportFormat = None,
                           filename: str = None) -> str:
        """Export translations to a file.
        
        Args:
            translations: List of translation records
            format: Export format (defaults to config)
            filename: Output filename (auto-generated if not provided)
            
        Returns:
            Path to the exported file
        """
        fmt = format or self.config.format
        
        if not filename:
            filename = self._generate_filename("translations", fmt)
        
        filepath = os.path.join(self.config.output_dir, filename)
        
        if fmt == ExportFormat.TXT:
            self._export_txt(translations, filepath)
        elif fmt == ExportFormat.CSV:
            self._export_csv(translations, filepath)
        elif fmt == ExportFormat.JSON:
            self._export_json(translations, filepath)
        elif fmt == ExportFormat.HTML:
            self._export_html(translations, filepath)
        elif fmt == ExportFormat.SRT:
            self._export_srt(translations, filepath)
        elif fmt == ExportFormat.PDF:
            self._export_pdf(translations, filepath)
        
        return filepath
    
    def _export_txt(self, translations: List[TranslationRecord], filepath: str):
        """Export to plain text file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SIGN LANGUAGE TRANSLATION EXPORT\n")
            f.write(f"Generated: {datetime.now().strftime(self.config.date_format)}\n")
            f.write("=" * 60 + "\n\n")
            
            for record in translations:
                line = ""
                if self.config.include_timestamps:
                    line += f"[{record.timestamp.strftime(self.config.date_format)}] "
                
                line += record.text
                
                if self.config.include_confidence:
                    line += f" (confidence: {record.confidence:.0%})"
                
                f.write(line + "\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"Total translations: {len(translations)}\n")
    
    def _export_csv(self, translations: List[TranslationRecord], filepath: str):
        """Export to CSV file."""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            header = ['Text']
            if self.config.include_timestamps:
                header.insert(0, 'Timestamp')
            if self.config.include_confidence:
                header.append('Confidence')
            if self.config.include_gesture_types:
                header.append('Gesture Type')
            
            writer.writerow(header)
            
            # Data
            for record in translations:
                row = [record.text]
                if self.config.include_timestamps:
                    row.insert(0, record.timestamp.strftime(self.config.date_format))
                if self.config.include_confidence:
                    row.append(f"{record.confidence:.2%}")
                if self.config.include_gesture_types:
                    row.append(record.gesture_type)
                
                writer.writerow(row)
    
    def _export_json(self, translations: List[TranslationRecord], filepath: str):
        """Export to JSON file."""
        data = {
            'export_date': datetime.now().isoformat(),
            'total_count': len(translations),
            'translations': []
        }
        
        for record in translations:
            item = {'text': record.text}
            if self.config.include_timestamps:
                item['timestamp'] = record.timestamp.isoformat()
            if self.config.include_confidence:
                item['confidence'] = record.confidence
            if self.config.include_gesture_types:
                item['gesture_type'] = record.gesture_type
            
            data['translations'].append(item)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _export_html(self, translations: List[TranslationRecord], filepath: str):
        """Export to HTML file."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sign Language Translation Export</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #fff; }
        h1 { color: #8b5cf6; border-bottom: 2px solid #8b5cf6; padding-bottom: 10px; }
        .translation { background: #242432; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #06b6d4; }
        .timestamp { color: #94a3b8; font-size: 12px; }
        .text { font-size: 18px; margin: 8px 0; }
        .confidence { color: #10b981; font-size: 12px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #2d2d3d; color: #64748b; }
    </style>
</head>
<body>
    <h1>✋ Sign Language Translation Export</h1>
    <p>Generated: """ + datetime.now().strftime(self.config.date_format) + """</p>
    <div class="translations">
"""
        
        for record in translations:
            html += '<div class="translation">\n'
            if self.config.include_timestamps:
                html += f'<div class="timestamp">{record.timestamp.strftime(self.config.date_format)}</div>\n'
            html += f'<div class="text">{record.text}</div>\n'
            if self.config.include_confidence:
                html += f'<div class="confidence">Confidence: {record.confidence:.0%}</div>\n'
            html += '</div>\n'
        
        html += f"""
    </div>
    <div class="footer">
        Total translations: {len(translations)}
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _export_srt(self, translations: List[TranslationRecord], filepath: str):
        """Export to SRT subtitle format."""
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, record in enumerate(translations, 1):
                # Calculate start and end times
                start_time = record.timestamp
                duration = record.duration if record.duration > 0 else 2.0
                
                # Format as SRT timestamp (HH:MM:SS,mmm)
                start_str = self._format_srt_time(0)  # Would need actual video timing
                end_str = self._format_srt_time(duration)
                
                f.write(f"{i}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{record.text}\n\n")
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT timestamp."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _export_pdf(self, translations: List[TranslationRecord], filepath: str):
        """Export to PDF file (requires reportlab)."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#8b5cf6'),
                spaceAfter=30
            )
            story.append(Paragraph("Sign Language Translation Export", title_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime(self.config.date_format)}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Translations table
            data = [['#', 'Timestamp', 'Translation', 'Confidence']]
            for i, record in enumerate(translations, 1):
                data.append([
                    str(i),
                    record.timestamp.strftime("%H:%M:%S"),
                    record.text,
                    f"{record.confidence:.0%}"
                ])
            
            table = Table(data, colWidths=[30, 80, 300, 70])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1a1a2e')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(table)
            
            doc.build(story)
            
        except ImportError:
            # Fallback to text if reportlab not available
            self._export_txt(translations, filepath.replace('.pdf', '.txt'))
            print("⚠️ PDF export requires 'reportlab'. Exported as TXT instead.")
    
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to system clipboard."""
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except ImportError:
            try:
                # Fallback for Windows
                import subprocess
                subprocess.run(['clip'], input=text.encode('utf-8'), check=True)
                return True
            except:
                return False
    
    def get_shareable_text(self, translations: List[TranslationRecord]) -> str:
        """Generate shareable text summary."""
        if not translations:
            return ""
        
        lines = []
        lines.append("📝 Sign Language Translation")
        lines.append("-" * 30)
        
        for record in translations:
            lines.append(f"• {record.text}")
        
        lines.append("-" * 30)
        lines.append(f"Translated with SignLang App")
        
        return "\n".join(lines)


# Singleton instance
export_manager = ExportManager()
