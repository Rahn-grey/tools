"""
Printer detection and management for Windows and Linux.
Uses native Python libraries (pywin32 for Windows, lp for Linux).
"""
import subprocess
import sys
import os
import time
import tempfile
from typing import List, Dict, Optional


class PrinterManager:
    """Manages printer detection and print jobs across platforms."""

    def __init__(self):
        self.platform = sys.platform
        self._cached_printers = None

    def get_printers(self) -> List[Dict]:
        """Get list of available printers."""
        if self.platform == 'win32':
            return self._get_windows_printers()
        else:
            return self._get_linux_printers()

    def _get_windows_printers(self) -> List[Dict]:
        """Get printers on Windows using pywin32."""
        printers = []
        try:
            import win32print
            printers_enum = win32print.EnumPrinters(2)  # PRINTER_ENUM_LOCAL
            default_printer = win32print.GetDefaultPrinter()

            for printer in printers_enum:
                printers.append({
                    'name': printer[2],
                    'is_default': printer[2] == default_printer,
                    'status': 'ready'
                })
        except ImportError:
            print("pywin32 not installed. Run: pip install pywin32")
            return []
        except Exception as e:
            print(f"Error getting printers: {e}")
            return []

        return printers

    def _get_linux_printers(self) -> List[Dict]:
        """Get printers on Linux using CUPS."""
        printers = []
        try:
            result = subprocess.run(
                ['lpstat', '-p'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith('printer '):
                        parts = line.split()
                        name = parts[1]
                        status = 'ready' if 'idle' in line.lower() or 'ready' in line.lower() else 'busy'
                        printers.append({
                            'name': name,
                            'is_default': False,
                            'status': status
                        })

            # Check default
            result = subprocess.run(
                ['lpstat', '-d'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and 'no default' not in result.stdout.lower():
                default = result.stdout.split(':')[1].strip()
                for p in printers:
                    if p['name'] == default:
                        p['is_default'] = True
        except Exception:
            pass

        return printers

    def print_file(self, printer_name: str, file_path: str, copies: int = 1,
                   page_range: str = '', orientation: str = 'portrait',
                   paper_size: str = 'auto', paper_source: str = 'auto',
                   scaling: int = 100, print_quality: str = 'auto',
                   color_mode: str = 'auto', duplex: str = 'none',
                   collate: bool = True) -> Dict:
        """Send a file to the specified printer."""
        if not printer_name or not file_path:
            return {'success': False, 'error': 'Missing printer or file'}

        if not os.path.exists(file_path):
            return {'success': False, 'error': f'File not found: {file_path}'}

        if self.platform == 'win32':
            return self._print_windows(printer_name, file_path, copies, page_range,
                                      orientation, paper_size, paper_source,
                                      scaling, print_quality, color_mode, duplex, collate)
        else:
            return self._print_linux(printer_name, file_path, copies, page_range,
                                      orientation, paper_size, paper_source,
                                      scaling, print_quality, color_mode, duplex, collate)

    def _print_windows(self, printer_name: str, file_path: str, copies: int,
                       page_range: str, orientation: str, paper_size: str,
                       paper_source: str, scaling: int, print_quality: str,
                       color_mode: str, duplex: str, collate: bool) -> Dict:
        """Print file on Windows."""
        ext = file_path.lower().split('.')[-1]

        # For PDFs, try SumatraPDF first (best for CLI printing with page range support)
        if ext == 'pdf':
            sumatra_path = self._find_sumatra_pdf()
            if sumatra_path:
                return self._print_pdf_sumatra(sumatra_path, printer_name, file_path,
                                             copies, page_range, orientation, scaling,
                                             color_mode, duplex)
            else:
                return {'success': False, 'error': 'PDF打印机未找到，请安装SumatraPDF'}

        # For Office files, try LibreOffice
        if ext in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp']:
            result = self._print_with_libreoffice(printer_name, file_path, copies, page_range)
            if result.get('success'):
                return result
            return result # error message already set

        # For image files, convert to PDF via Pillow + ReportLab, then print
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp']:
            result = self._print_image(printer_name, file_path, copies, orientation,
                                       paper_size, scaling, color_mode)
            if result.get('success'):
                return result
            return result

        return {'success': False, 'error': '不支持的文件类型'}

    def _print_with_libreoffice(self, printer_name: str, file_path: str, copies: int, page_range: str = '') -> Dict:
        """Print using LibreOffice command line."""
        import shutil
        # First check environment variable (custom path)
        custom_path = os.environ.get('SOFFICE_PATH')
        if custom_path and os.path.exists(custom_path):
            soffice_path = custom_path
        else:
            # Then check PATH environment variable
            soffice_path = shutil.which('soffice') or shutil.which('soffice.exe')
            if not soffice_path:
                # Then check common installation paths
                soffice_paths = [
                    os.path.join(os.environ.get('ProgramFiles'), 'LibreOffice', 'Program', 'soffice.exe'),
                    os.path.join(os.environ.get('ProgramFiles(x86)'), 'LibreOffice', 'Program', 'soffice.exe'),
                ]
                for path in soffice_paths:
                    if os.path.exists(path):
                        soffice_path = path
                        break

        if not soffice_path:
            return {'success': False, 'error': 'LibreOffice not found'}

        try:
            # Convert once to PDF (LibreOffice handles copies at print time)
            cmd = [
                soffice_path,
                '--headless',
                '--invisible',
                '--nodefault',
                '--nofirststartwizard',
                '--convert-to', 'pdf',
                '--outdir', tempfile.gettempdir(),
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                return {'success': False, 'error': f'LibreOffice failed: {result.stderr}'}

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            pdf_path = os.path.join(tempfile.gettempdir(), f"{base_name}.pdf")

            if not os.path.exists(pdf_path):
                return {'success': False, 'error': 'PDF conversion failed'}

            # Print PDF using SumatraPDF (supports copies internally)
            sumatra_path = self._find_sumatra_pdf()
            if sumatra_path:
                sumatra_result = self._print_pdf_sumatra(
                    sumatra_path, printer_name, pdf_path,
                    copies, page_range, 'portrait', 100, 'auto', 'none'
                )
            else:
                sumatra_result = {'success': False, 'error': 'PDF打印机未找到，请安装SumatraPDF'}

            try:
                os.remove(pdf_path)
            except Exception:
                pass

            return sumatra_result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _print_pdf_sumatra(self, sumatra_path: str, printer_name: str, file_path: str,
                           copies: int, page_range: str, orientation: str, scaling: int,
                           color_mode: str, duplex: str) -> Dict:
        """Print PDF using SumatraPDF command line."""
        try:
            cmd_args = [sumatra_path, '-print-to', printer_name, '-exit-on-print']

            # Build print settings
            settings = []

            if page_range:
                settings.append(page_range)  # 直接用页码，如 "1-3" 或 "1,3,5"

            if orientation == 'landscape':
                settings.append('landscape')
            elif orientation == 'portrait':
                settings.append('portrait')

            if copies > 1:
                settings.append(f'copies={copies}')

            if color_mode == 'grayscale':
                settings.append('grayscale')

            if duplex == 'long':
                settings.append('duplexlong')
            elif duplex == 'short':
                settings.append('duplexshort')

            if scaling != 100:
                settings.append(f'scale={scaling}')

            if settings:
                cmd_args.extend(['-print-settings', ','.join(settings)])

            cmd_args.append(os.path.abspath(file_path))

            result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {'success': True, 'job_id': f'sumatra-{os.path.basename(file_path)}'}
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                return {'success': False, 'error': error_msg or 'SumatraPDF print failed'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _find_sumatra_pdf(self) -> Optional[str]:
        """Find SumatraPDF executable."""
        import shutil
        # First check environment variable (custom path)
        custom_path = os.environ.get('SUMATRA_PDF_PATH')
        if custom_path and os.path.exists(custom_path):
            return custom_path
        # Then check PATH environment variable
        for name in ['SumatraPDF', 'SumatraPDF.exe', 'sumatrapdf', 'sumatrapdf.exe']:
            path = shutil.which(name)
            if path:
                return path
        # Then check common installation paths
        possible_paths = [
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'SumatraPDF', 'SumatraPDF.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'SumatraPDF', 'SumatraPDF.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'SumatraPDF', 'SumatraPDF.exe'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'SumatraPDF', 'SumatraPDF.exe'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _print_linux(self, printer_name: str, file_path: str, copies: int,
                     page_range: str, orientation: str, paper_size: str,
                     paper_source: str, scaling: int, print_quality: str,
                     color_mode: str, duplex: str, collate: bool) -> Dict:
        """Print file on Linux using CUPS lp command."""
        try:
            cmd = ['lp']

            if page_range:
                cmd.extend(['-P', page_range])

            if copies > 1:
                cmd.extend(['-n', str(copies)])

            if collate:
                cmd.extend(['-o', 'collate=true'])

            if orientation == 'landscape':
                cmd.extend(['-o', 'orientation=landscape'])
            elif orientation == 'portrait':
                cmd.extend(['-o', 'orientation=portrait'])

            if paper_size != 'auto':
                cmd.extend(['-o', f'media={paper_size}'])

            if paper_source != 'auto':
                cmd.extend(['-o', f'paper-source={paper_source}'])

            if scaling != 100:
                cmd.extend(['-o', f'scaling={scaling}'])

            if print_quality == 'draft':
                cmd.extend(['-o', 'print-quality=3'])
            elif print_quality in ('high', 'best'):
                cmd.extend(['-o', 'print-quality=5'])

            if color_mode == 'grayscale':
                cmd.extend(['-o', 'ColorModel=KGray'])
            elif color_mode == 'color':
                cmd.extend(['-o', 'ColorModel=RGB'])

            if duplex == 'long':
                cmd.extend(['-o', 'sides=two-sided-long-edge'])
            elif duplex == 'short':
                cmd.extend(['-o', 'sides=two-sided-short-edge'])

            cmd.extend(['-d', printer_name, file_path])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {'success': True, 'job_id': f'lp-{os.path.basename(file_path)}'}
            else:
                return {'success': False, 'error': result.stderr}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _print_image(self, printer_name: str, file_path: str, copies: int, orientation: str,
                     paper_size: str = 'auto', scaling: int = 100,
                     color_mode: str = 'auto') -> Dict:
        """Print image by converting to PDF first, then printing via SumatraPDF/LibreOffice."""
        return self._print_image_via_pdf(printer_name, file_path, copies, orientation,
                                         scaling, color_mode)

    def _print_image_sumatra(self, sumatra_path: str, printer_name: str, file_path: str,
                              copies: int, orientation: str, paper_size: str,
                              scaling: int, color_mode: str) -> Dict:
        """Print image directly via SumatraPDF command line."""
        try:
            cmd_args = [sumatra_path, '-print-to', printer_name, '-exit-on-print']

            settings = []

            # 纸张
            if paper_size != 'auto':
                paper_map = {'A4': 'A4', 'A5': 'A5', 'A3': 'A3',
                             'Letter': 'Letter', 'Legal': 'Legal'}
                if paper_size in paper_map:
                    settings.append(paper_map[paper_size])

            # 方向
            if orientation == 'landscape':
                settings.append('landscape')
            else:
                settings.append('portrait')

            # 份数
            if copies > 1:
                settings.append(f'copies={copies}')

            # 灰度
            if color_mode == 'grayscale':
                settings.append('grayscale')

            # 缩放
            if scaling != 100:
                settings.append(f'scale={scaling}')

            if settings:
                cmd_args.extend(['-print-settings', ','.join(settings)])

            cmd_args.append(os.path.abspath(file_path))

            result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {'success': True, 'job_id': f'img-{os.path.basename(file_path)}'}
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                return {'success': False, 'error': error_msg or 'SumatraPDF 打印图片失败'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _print_image_via_pdf(self, printer_name: str, file_path: str, copies: int,
                              orientation: str, scaling: int,
                              color_mode: str = 'auto') -> Dict:
        """Convert image to PDF via ReportLab then print via SumatraPDF/LibreOffice."""
        try:
            from PIL import Image
        except ImportError:
            return {'success': False, 'error': 'Pillow 未安装，请运行: pip install Pillow'}

        try:
            img = Image.open(file_path)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            pdf_path = os.path.join(tempfile.gettempdir(), f"{base_name}.pdf")

            # A4 尺寸（磅，1 inch = 72磅）
            a4_w, a4_h = 595, 842
            if orientation == 'landscape':
                a4_w, a4_h = a4_h, a4_w

            img_w, img_h = img.size
            fill_ratio = scaling / 100.0
            max_w = a4_w * fill_ratio
            max_h = a4_h * fill_ratio
            ratio = min(max_w / img_w, max_h / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            x = (a4_w - new_w) / 2
            y = (a4_h - new_h) / 2

            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4

            page_size = A4 if orientation != 'landscape' else (A4[1], A4[0])
            c = canvas.Canvas(pdf_path, pagesize=page_size)
            c.drawImage(file_path, x, y, width=new_w, height=new_h)
            c.save()

            # 打印 PDF — ReportLab 已设置正确的页面尺寸/方向，无需再传 orientation
            sumatra_path = self._find_sumatra_pdf()
            if sumatra_path:
                result = self._print_pdf_sumatra(
                    sumatra_path, printer_name, pdf_path,
                    copies, '', '', scaling, color_mode, 'none'
                )
            else:
                result = self._print_with_libreoffice(printer_name, pdf_path, copies, '')

            try:
                os.remove(pdf_path)
            except Exception:
                pass
            return result

        except ImportError:
            return {'success': False, 'error': 'reportlab 未安装，请运行: pip install reportlab'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_printer_status(self, printer_name: str) -> Dict:
        """Get status of a specific printer."""
        printers = self.get_printers()
        for p in printers:
            if p['name'] == printer_name:
                return {
                    'success': True,
                    'name': p['name'],
                    'status': p.get('status', 'unknown'),
                    'is_default': p.get('is_default', False)
                }
        return {'success': False, 'error': 'Printer not found'}


if __name__ == '__main__':
    pm = PrinterManager()
    print("Available printers:")
    for p in pm.get_printers():
        print(f"  - {p['name']} {'(default)' if p.get('is_default') else ''}")