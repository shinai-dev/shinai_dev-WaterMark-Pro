import os
import json
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw, ImageStat
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, font as tkfont
from matplotlib import font_manager
import threading
import time

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WaterMark Pro")
        self.root.geometry("850x700")
        self.set_minimalist_theme()
        self.config = self.load_settings()
        self.font_map = self.get_system_fonts()
        self.processing = False
        self.current_language = self.config.get("language", "english")
        self.languages = {
            "en": self.load_english(),
            "es": self.load_spanish(),
            "ja": self.load_japanese(),
            "zh": self.load_chinese(),
            "ko": self.load_korean()
        }
        self.setup_ui()
        self.update_language()
        
    def set_minimalist_theme(self):
        self.bg_color = "#f5f5f7"
        self.text_color = "#333333"
        self.accent_color = "#007aff"
        self.error_color = "#ff3b30"
        self.success_color = "#34c759"
        self.secondary_color = "#8e8e93"
        self.font_family = "Helvetica"
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure styles
        self.style.configure('.', 
                          background=self.bg_color,
                          foreground=self.text_color,
                          font=(self.font_family, 11))
        
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TEntry', 
                          fieldbackground="white",
                          foreground=self.text_color,
                          insertcolor=self.text_color,
                          bordercolor="#c7c7cc",
                          relief="solid",
                          padding=8)
        self.style.configure('TCombobox', 
                          fieldbackground="white",
                          foreground=self.text_color,
                          selectbackground="#e5e5ea",
                          selectforeground=self.text_color,
                          bordercolor="#c7c7cc")
        self.style.configure('TButton', 
                          background="white",
                          foreground=self.accent_color,
                          bordercolor="#c7c7cc",
                          padding=8,
                          font=(self.font_family, 11, 'bold'))
        self.style.map('TButton',
                    background=[('active', '#e5e5ea')],
                    foreground=[('active', self.accent_color)])
        self.style.configure('Horizontal.TProgressbar',
                          background=self.accent_color,
                          troughcolor="#e5e5ea",
                          bordercolor="#c7c7cc",
                          lightcolor=self.accent_color,
                          darkcolor=self.accent_color)
        self.style.configure('TScale',
                          background=self.bg_color,
                          troughcolor="#e5e5ea",
                          foreground=self.text_color,
                          bordercolor="#c7c7cc")
        self.style.configure('TCheckbutton',
                          background=self.bg_color,
                          foreground=self.text_color)
        self.style.configure('TRadiobutton',
                          background=self.bg_color,
                          foreground=self.text_color)

    def load_settings(self):
        os.makedirs("setting", exist_ok=True)
        config_path = "setting/setting.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "font_percent": 5,
            "font_file": "Arial",
            "opacity": 180,
            "last_folder": "",
            "auto_color": True,
            "language": "english"
        }

    def get_system_fonts(self):
        font_paths = font_manager.findSystemFonts(fontext='ttf')
        font_map = {}
        for path in font_paths:
            try:
                name = os.path.splitext(os.path.basename(path))[0]
                font_map[name] = path
            except:
                continue
        return dict(sorted(font_map.items())) or {"Arial": font_manager.findfont("Arial")}

    def setup_ui(self):
        # Main frame with improved spacing
        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with language selector
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.header_label = ttk.Label(
            header_frame,
            text="WaterMark Pro",
            font=(self.font_family, 18, 'bold'),
            foreground=self.accent_color
        )
        self.header_label.pack(side=tk.LEFT)
        
        # Language selection
        self.language_var = tk.StringVar(value=self.current_language)
        lang_menu = ttk.OptionMenu(
            header_frame,
            self.language_var,
            self.current_language.capitalize(),
            *[lang.capitalize() for lang in self.languages.keys()],
            command=self.change_language
        )
        lang_menu.pack(side=tk.RIGHT, padx=10)
        
        # Status label
        self.status_label = ttk.Label(
            header_frame,
            text="Status: Ready",
            foreground=self.secondary_color
        )
        self.status_label.pack(side=tk.RIGHT)

        # Configuration panel
        config_frame = ttk.LabelFrame(
            self.main_frame,
            padding=(20, 15))
        config_frame.pack(fill=tk.X, pady=(0, 15))

        # Image folder
        ttk.Label(config_frame, text="Image directory:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_path = ttk.Entry(config_frame, width=60)
        self.entry_path.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.entry_path.insert(0, self.config.get("last_folder", ""))
        
        browse_btn = ttk.Button(config_frame, text="Browse", command=self.browse_folder)
        browse_btn.grid(row=0, column=2, padx=5)

        # Watermark text
        ttk.Label(config_frame, text="Watermark text:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_text = ttk.Entry(config_frame, width=60)
        self.entry_text.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        # Font size
        ttk.Label(config_frame, text="Font size (%):").grid(row=2, column=0, sticky="w", pady=5)
        self.font_size_spin = ttk.Spinbox(config_frame, from_=1, to=50, width=5)
        self.font_size_spin.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        self.font_size_spin.set(self.config.get("font_percent", 5))

        # Opacity
        ttk.Label(config_frame, text="Opacity:").grid(row=3, column=0, sticky="w", pady=5)
        self.opacity_slider = ttk.Scale(
            config_frame, 
            from_=0, 
            to=255, 
            orient=tk.HORIZONTAL,
            length=200
        )
        self.opacity_slider.set(self.config.get("opacity", 180))
        self.opacity_slider.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        self.opacity_value = ttk.Label(config_frame, text=str(self.config.get("opacity", 180)))
        self.opacity_value.grid(row=3, column=2, sticky="w", padx=5)
        self.opacity_slider.bind("<Motion>", lambda e: self.opacity_value.config(
            text=str(int(self.opacity_slider.get()))))

        # Auto color adjustment
        self.auto_color_var = tk.BooleanVar(value=self.config.get("auto_color", True))
        auto_color_cb = ttk.Checkbutton(
            config_frame,
            text="Automatic color adjustment",
            variable=self.auto_color_var,
            command=self.toggle_color_controls
        )
        auto_color_cb.grid(row=4, column=0, columnspan=3, sticky="w", pady=5)

        # Font selector
        ttk.Label(config_frame, text="Font:").grid(row=5, column=0, sticky="w", pady=5)
        self.font_search_var = tk.StringVar()
        self.font_choice = ttk.Combobox(
            config_frame, 
            textvariable=self.font_search_var,
            values=list(self.font_map.keys()), 
            state="normal",
            width=58
        )
        self.font_choice.grid(row=5, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        self.font_choice.set(self.config.get("font_file", "Arial"))
        self.font_search_var.trace("w", self.filter_fonts)

        # Action buttons
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 15))

        self.process_btn = ttk.Button(
            action_frame,
            text="START PROCESS",
            command=self.start_processing,
            style='TButton'
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(
            action_frame,
            text="CANCEL",
            command=self.cancel_processing,
            style='TButton'
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        self.cancel_btn.state(['disabled'])

        # Console
        console_frame = ttk.LabelFrame(
            self.main_frame,
            padding=(15, 10))
        console_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.console = tk.Text(
            console_frame,
            bg="white",
            fg=self.text_color,
            insertbackground=self.text_color,
            wrap=tk.WORD,
            font=(self.font_family, 10),
            height=10,
            padx=10,
            pady=10,
            relief="solid",
            borderwidth=1
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.insert(tk.END, "System initialized. Ready to process images.\n")
        self.console.config(state=tk.DISABLED)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.main_frame,
            orient=tk.HORIZONTAL,
            length=100,
            mode='determinate',
            style='Horizontal.TProgressbar'
        )
        self.progress.pack(fill=tk.X)

        # Configure column weights
        config_frame.columnconfigure(1, weight=1)

    def toggle_color_controls(self):
        pass  # Placeholder for future functionality

    def filter_fonts(self, *args):
        search_term = self.font_search_var.get().lower()
        font_names = list(self.font_map.keys())
        if search_term == "":
            self.font_choice['values'] = font_names
        else:
            filtered = [f for f in font_names if search_term in f.lower()]
            self.font_choice['values'] = filtered

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, folder_selected)
            self.config["last_folder"] = folder_selected
            self.log(self.translate("Selected directory:") + f" {folder_selected}")

    def log(self, message):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, f"{message}\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def start_processing(self):
        if self.processing:
            return
            
        folder = self.entry_path.get()
        if not folder or not os.path.isdir(folder):
            self.log(self.translate("Error: Invalid directory"))
            messagebox.showerror(self.translate("Error"), self.translate("Please select a valid directory"))
            return
            
        self.processing = True
        self.process_btn.state(['disabled'])
        self.cancel_btn.state(['!disabled'])
        self.status_label.config(text=self.translate("Status: Processing..."), foreground=self.accent_color)
        
        # Start processing in separate thread
        threading.Thread(target=self.process_images_thread, daemon=True).start()

    def cancel_processing(self):
        if self.processing:
            self.processing = False
            self.log(self.translate("Process canceled by user"))
            self.status_label.config(text=self.translate("Status: Canceled"), foreground=self.error_color)

    def process_images_thread(self):
        try:
            folder = self.entry_path.get()
            watermark_text = self.entry_text.get()
            font_percent = int(self.font_size_spin.get())
            font_name = self.font_choice.get()
            opacity = int(self.opacity_slider.get())
            auto_color = self.auto_color_var.get()

            # Update configuration
            self.config.update({
                "font_percent": font_percent,
                "font_file": font_name,
                "opacity": opacity,
                "last_folder": folder,
                "auto_color": auto_color,
                "language": self.current_language
            })
            
            with open("setting/setting.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)

            font_path = self.font_map.get(font_name)
            if not font_path:
                self.log(self.translate("Error: Font not found -") + f" {font_name}")
                messagebox.showerror(self.translate("Error"), self.translate("Font not found:") + f" {font_name}")
                return

            images = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            total = len(images)
            
            if not images:
                self.log(self.translate("Error: No images found in directory"))
                messagebox.showwarning(self.translate("Warning"), self.translate("No valid images found in directory"))
                return
                
            self.log(self.translate("Starting processing of") + f" {total} " + self.translate("images..."))
            
            for i, img_file in enumerate(images):
                if not self.processing:
                    break
                    
                img_path = os.path.join(folder, img_file)
                try:
                    # Update progress
                    progress = (i + 1) / total * 100
                    self.progress['value'] = progress
                    self.root.update()
                    
                    self.log(self.translate("Processing:") + f" {img_file}")
                    
                    with Image.open(img_path).convert("RGBA") as img:
                        # Determine watermark color based on image brightness if auto color is enabled
                        watermark_color = (255, 255, 255, opacity)  # Default white
                        if auto_color:
                            brightness = self.calculate_image_brightness(img)
                            self.log(f"{self.translate('Brightness:')} {brightness:.2f}")
                            if brightness > 128:  # Light background
                                watermark_color = (0, 0, 0, opacity)  # Black watermark
                                self.log(self.translate("Using black watermark for light background"))
                            else:
                                watermark_color = (255, 255, 255, opacity)  # White watermark
                                self.log(self.translate("Using white watermark for dark background"))
                        
                        self.apply_watermark(img, watermark_text, font_path, font_percent, watermark_color)
                        output_path = os.path.join(folder, f"wm_{img_file}")
                        img.save(output_path)
                    
                except Exception as e:
                    self.log(f"{self.translate('Error processing')} {img_file}: {str(e)}")
            
            if self.processing:
                self.log(f"{self.translate('Process completed.')} {len(images)} " + self.translate("images processed"))
                messagebox.showinfo(self.translate("Success"), f"{len(images)} " + self.translate("images processed with watermark."))
                self.status_label.config(text=self.translate("Status: Completed"), foreground=self.success_color)
        
        except Exception as e:
            self.log(f"{self.translate('Critical error:')} {str(e)}")
            messagebox.showerror(self.translate("Error"), f"{self.translate('An error occurred:')} {str(e)}")
            self.status_label.config(text=self.translate("Status: Error"), foreground=self.error_color)
        
        finally:
            self.processing = False
            self.progress['value'] = 0
            self.process_btn.state(['!disabled'])
            self.cancel_btn.state(['disabled'])
            if self.status_label['text'] not in (self.translate("Status: Canceled"), self.translate("Status: Error")):
                self.status_label.config(text=self.translate("Status: Ready"), foreground=self.secondary_color)

    def calculate_image_brightness(self, img):
        """Calculate average image brightness (0-255)"""
        # Convert to grayscale
        gray_img = img.convert('L')
        # Calculate statistics
        stat = ImageStat.Stat(gray_img)
        return stat.mean[0]

    def apply_watermark(self, img, text, font_path, font_percent, color):
        if not text:
            return
            
        width, height = img.size
        font_size = int((width + height) / 2 * font_percent / 100)

        try:
            with open(font_path, "rb") as f:
                font_bytes = BytesIO(f.read())
            font = ImageFont.truetype(font_bytes, font_size)
        except Exception as e:
            self.log(f"{self.translate('Error loading font:')} {str(e)} - " + self.translate("Using default font"))
            font = ImageFont.load_default()

        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Calculate centered position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position in bottom right corner with margin
        position = (width - text_width - 20, height - text_height - 20)
        
        draw.text(position, text, font=font, fill=color)
        img.alpha_composite(txt_layer)

    def change_language(self, language):
        self.current_language = language.lower()
        self.update_language()

    def update_language(self):
        lang = self.languages[self.current_language]
        
        # Update UI elements
        self.root.title(lang["title"])
        self.header_label.config(text=lang["title"])
        self.status_label.config(text=lang["status_ready"])
        
        # Configuration frame
        for i, text in enumerate(lang["config_labels"]):
            self.main_frame.winfo_children()[1].winfo_children()[i].config(text=text)
        
        # Buttons
        self.process_btn.config(text=lang["start_process"])
        self.cancel_btn.config(text=lang["cancel"])
        
        # Console
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, lang["console_ready"] + "\n")
        self.console.config(state=tk.DISABLED)
        
        # Update other UI elements as needed

    def translate(self, key):
        """Translate a key to current language"""
        return self.languages[self.current_language].get(key, key)

    def load_english(self):
        return {
            "title": "@shinai_dev WaterMark Pro",
            "status_ready": "Status: Ready",
            "status_processing": "Status: Processing...",
            "status_completed": "Status: Completed",
            "status_canceled": "Status: Canceled",
            "status_error": "Status: Error",
            "config_labels": [
                "Image directory:",
                "Watermark text:",
                "Select images",
                "Watermark text:",
                "Automatic color adjustment",
                "Font:"
            ],
            "start_process": "START PROCESS",
            "cancel": "CANCEL",
            "console_ready": "System initialized. Ready to process images.",
            "Selected directory:": "Selected directory:",
            "Error: Invalid directory": "Error: Invalid directory",
            "Please select a valid directory": "Please select a valid directory",
            "Process canceled by user": "Process canceled by user",
            "Error: Font not found -": "Error: Font not found -",
            "Font not found:": "Font not found:",
            "Error: No images found in directory": "Error: No images found in directory",
            "Warning": "Warning",
            "No valid images found in directory": "No valid images found in directory",
            "Starting processing of": "Starting processing of",
            "images...": "images...",
            "Processing:": "Processing:",
            "Brightness:": "Brightness:",
            "Using black watermark for light background": "Using black watermark for light background",
            "Using white watermark for dark background": "Using white watermark for dark background",
            "Error processing": "Error processing",
            "Process completed.": "Process completed.",
            "images processed": "images processed",
            "Success": "Success",
            "images processed with watermark.": "images processed with watermark.",
            "Critical error:": "Critical error:",
            "An error occurred:": "An error occurred:",
            "Error loading font:": "Error loading font:",
            "Using default font": "Using default font"
        }

    def load_spanish(self):
        return {
            "title": "@shinai_dev WaterMark Pro",
            "status_ready": "Estado: Listo",
            "status_processing": "Estado: Procesando...",
            "status_completed": "Estado: Completado",
            "status_canceled": "Estado: Cancelado",
            "status_error": "Estado: Error",
            "config_labels": [
                "Directorio de imágenes:",
                "Texto de marca de agua:",
                "Seleccionar las Imágenes:",
                "Texto de marca de agua:",
                "Ajuste automático de color",
                "Fuente:"
            ],
            "start_process": "INICIAR PROCESO",
            "cancel": "CANCELAR",
            "console_ready": "Sistema inicializado. Listo para procesar imágenes.",
            "Selected directory:": "Directorio seleccionado:",
            "Error: Invalid directory": "Error: Directorio no válido",
            "Please select a valid directory": "Por favor seleccione un directorio válido",
            "Process canceled by user": "Proceso cancelado por el usuario",
            "Error: Font not found -": "Error: Fuente no encontrada -",
            "Font not found:": "Fuente no encontrada:",
            "Error: No images found in directory": "Error: No se encontraron imágenes en el directorio",
            "Warning": "Advertencia",
            "No valid images found in directory": "No se encontraron imágenes válidas en el directorio",
            "Starting processing of": "Iniciando procesamiento de",
            "images...": "imágenes...",
            "Processing:": "Procesando:",
            "Brightness:": "Brillo:",
            "Using black watermark for light background": "Usando marca de agua negra para fondo claro",
            "Using white watermark for dark background": "Usando marca de agua blanca para fondo oscuro",
            "Error processing": "Error procesando",
            "Process completed.": "Proceso completado.",
            "images processed": "imágenes procesadas",
            "Success": "Éxito",
            "images processed with watermark.": "imágenes procesadas con marca de agua.",
            "Critical error:": "Error crítico:",
            "An error occurred:": "Ocurrió un error:",
            "Error loading font:": "Error cargando fuente:",
            "Using default font": "Usando fuente por defecto"
        }

    def load_japanese(self):
        return {
            "title": "@shinai_dev ウォーターマーク Pro",
            "status_ready": "状態: 準備完了",
            "status_processing": "状態: 処理中...",
            "status_completed": "状態: 完了",
            "status_canceled": "状態: キャンセル",
            "status_error": "状態: エラー",
            "config_labels": [
                "画像ディレクトリ:",
                "ウォーターマークテキスト:",
                "画像を選択する:",
                "ウォーターマークテキスト:",
                "自動色調整",
                "フォント:"
            ],
            "start_process": "処理開始",
            "cancel": "キャンセル",
            "console_ready": "システムが初期化されました。画像処理の準備ができています。",
            "Selected directory:": "選択されたディレクトリ:",
            "Error: Invalid directory": "エラー: 無効なディレクトリ",
            "Please select a valid directory": "有効なディレクトリを選択してください",
            "Process canceled by user": "ユーザーによって処理がキャンセルされました",
            "Error: Font not found -": "エラー: フォントが見つかりません -",
            "Font not found:": "フォントが見つかりません:",
            "Error: No images found in directory": "エラー: ディレクトリ内に画像が見つかりません",
            "Warning": "警告",
            "No valid images found in directory": "ディレクトリ内に有効な画像が見つかりません",
            "Starting processing of": "処理を開始します",
            "images...": "画像...",
            "Processing:": "処理中:",
            "Brightness:": "明るさ:",
            "Using black watermark for light background": "明るい背景に黒いウォーターマークを使用",
            "Using white watermark for dark background": "暗い背景に白いウォーターマークを使用",
            "Error processing": "処理エラー",
            "Process completed.": "処理が完了しました。",
            "images processed": "画像が処理されました",
            "Success": "成功",
            "images processed with watermark.": "画像にウォーターマークが追加されました。",
            "Critical error:": "重大なエラー:",
            "An error occurred:": "エラーが発生しました:",
            "Error loading font:": "フォントの読み込みエラー:",
            "Using default font": "デフォルトフォントを使用"
        }

    def load_chinese(self):
        return {
            "title": "@shinai_dev 水印专业版",
            "status_ready": "状态: 准备就绪",
            "status_processing": "状态: 处理中...",
            "status_completed": "状态: 完成",
            "status_canceled": "状态: 已取消",
            "status_error": "状态: 错误",
            "config_labels": [
                "图片目录:",
                "水印文字:",
                "选择图片:",
                "水印文字:",
                "自动颜色调整",
                "字体:"
            ],
            "start_process": "开始处理",
            "cancel": "取消",
            "console_ready": "系统已初始化。准备处理图片。",
            "Selected directory:": "已选择目录:",
            "Error: Invalid directory": "错误: 无效目录",
            "Please select a valid directory": "请选择有效目录",
            "Process canceled by user": "用户取消了处理",
            "Error: Font not found -": "错误: 未找到字体 -",
            "Font not found:": "未找到字体:",
            "Error: No images found in directory": "错误: 目录中未找到图片",
            "Warning": "警告",
            "No valid images found in directory": "目录中未找到有效图片",
            "Starting processing of": "开始处理",
            "images...": "张图片...",
            "Processing:": "正在处理:",
            "Brightness:": "亮度:",
            "Using black watermark for light background": "浅色背景使用黑色水印",
            "Using white watermark for dark background": "深色背景使用白色水印",
            "Error processing": "处理错误",
            "Process completed.": "处理完成。",
            "images processed": "张图片已处理",
            "Success": "成功",
            "images processed with watermark.": "张图片已添加水印。",
            "Critical error:": "严重错误:",
            "An error occurred:": "发生错误:",
            "Error loading font:": "加载字体错误:",
            "Using default font": "使用默认字体"
        }

    def load_korean(self):
        return {
            "title": "@shinai_dev 워터마크 Pro",
            "status_ready": "상태: 준비됨",
            "status_processing": "상태: 처리 중...",
            "status_completed": "상태: 완료",
            "status_canceled": "상태: 취소됨",
            "status_error": "상태: 오류",
            "config_labels": [
                "이미지 디렉토리:",
                "워터마크 텍스트:",
                "이미지 선택:",
                "워터마크 텍스트:",
                "자동 색상 조정",
                "글꼴:"
            ],
            "start_process": "처리 시작",
            "cancel": "취소",
            "console_ready": "시스템이 초기화되었습니다. 이미지 처리 준비가 되었습니다.",
            "Selected directory:": "선택된 디렉토리:",
            "Error: Invalid directory": "오류: 유효하지 않은 디렉토리",
            "Please select a valid directory": "유효한 디렉토리를 선택하세요",
            "Process canceled by user": "사용자에 의해 처리 취소됨",
            "Error: Font not found -": "오류: 글꼴을 찾을 수 없음 -",
            "Font not found:": "글꼴을 찾을 수 없음:",
            "Error: No images found in directory": "오류: 디렉토리에서 이미지를 찾을 수 없음",
            "Warning": "경고",
            "No valid images found in directory": "디렉토리에서 유효한 이미지를 찾을 수 없음",
            "Starting processing of": "처리 시작",
            "images...": "개의 이미지...",
            "Processing:": "처리 중:",
            "Brightness:": "밝기:",
            "Using black watermark for light background": "밝은 배경에 검은색 워터마크 사용",
            "Using white watermark for dark background": "어두운 배경에 흰색 워터마크 사용",
            "Error processing": "처리 오류",
            "Process completed.": "처리 완료.",
            "images processed": "개의 이미지 처리됨",
            "Success": "성공",
            "images processed with watermark.": "개의 이미지에 워터마크 추가됨.",
            "Critical error:": "심각한 오류:",
            "An error occurred:": "오류가 발생했습니다:",
            "Error loading font:": "글꼴 로딩 오류:",
            "Using default font": "기본 글꼴 사용"
        }

    def on_closing(self):
        if self.processing:
            if messagebox.askokcancel(
                self.translate("Exit"), 
                self.translate("Processing is running. Do you want to cancel and exit?")
            ):
                self.processing = False
                time.sleep(0.5)  # Give the thread time to finish
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()