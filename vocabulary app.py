import json
import os
import random
import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ===================== 数据库配置 =====================
DB_FILE = "words_database.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_words():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        migrated = False
        for word in data:
            if "examples" not in word:
                word["examples"] = []
                old_en = word.get("sentence_en", "").strip()
                old_cn = word.get("sentence_cn", "").strip()
                if old_en or old_cn:
                    word["examples"].append({"en": old_en, "cn": old_cn})
                word.pop("sentence_en", None)
                word.pop("sentence_cn", None)
                migrated = True
        if migrated:
            save_words(data)
        return data

def save_words(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

init_db()


def format_chinese_meaning(chinese_text):
    if not chinese_text:
        return ""
    pattern = r'(\b(?:adj|v|n|adv|prep|conj|pron|num|art|int|interj|abbr)\.)\s*'
    parts = re.split(pattern, chinese_text, flags=re.IGNORECASE)
    result_parts = []
    for i, part in enumerate(parts):
        if i > 0 and re.match(pattern, part, re.IGNORECASE):
            result_parts.append(f"\n  {part}")
        else:
            result_parts.append(part)
    formatted = "".join(result_parts).strip()
    if formatted and not formatted.startswith("  "):
        formatted = "  " + formatted
    formatted = re.sub(r'\n\s*\n', '\n', formatted)
    return formatted

# ===================== 主程序 =====================
class WordBookApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("英语单词本")
        self.geometry("800x550")
        self.minsize(500, 550)

        self.word_list = load_words()

        # 主容器：菜单页面 + 功能页面
        self.menu_frame = ttk.Frame(self)
        self.function_frame = ttk.Frame(self)

        self.menu_frame.pack(fill=tk.BOTH, expand=True)
        self.function_frame.pack(fill=tk.BOTH, expand=True)
        self.function_frame.pack_forget()

        self.build_menu()
        self.build_list_page()
        self.build_edit_page()
        self.build_test_page()

        self.current_page = None

    # ========== 菜单：三个卡片 ==========
    def build_menu(self):
        center_frame = ttk.Frame(self.menu_frame)
        center_frame.pack(expand=True)

        card_width, card_height = 180, 180
        padding = 25

        def make_card(parent, col, bg, icon, text, page_name):
            card = tk.Canvas(parent, width=card_width, height=card_height, bg=bg, highlightthickness=0)
            card.grid(row=0, column=col, padx=padding, pady=padding)
            card.create_text(card_width//2, card_height//2 - 20, text=icon, font=("Segoe UI", 44), fill="white")
            card.create_text(card_width//2, card_height//2 + 30, text=text, font=("微软雅黑", 12, "bold"), fill="white")
            card.bind("<Button-1>", lambda e, p=page_name: self.show_function_page(p))
            card.bind("<Enter>", lambda e, c=card, bg=bg: c.config(bg=self._darken_color(bg)))
            card.bind("<Leave>", lambda e, c=card, bg=bg: c.config(bg=bg))
            return card

        make_card(center_frame, 0, "#3498db", "📖", "单词列表", "list")
        make_card(center_frame, 1, "#2ecc71", "✏️", "增删改查", "edit")
        make_card(center_frame, 2, "#e67e22", "🎴", "卡片自测", "test")

    @staticmethod
    def _darken_color(hex_color):
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (1,3,5))
        darker = tuple(max(0, int(c * 0.8)) for c in rgb)
        return f"#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}"

    def show_function_page(self, page_name):
        self.menu_frame.pack_forget()
        self.function_frame.pack(fill=tk.BOTH, expand=True)

        self.frame_list.pack_forget()
        self.frame_edit.pack_forget()
        self.frame_test.pack_forget()

        if page_name == "list":
            self.frame_list.pack(fill=tk.BOTH, expand=True)
            self.refresh_list_page()
        elif page_name == "edit":
            self.frame_edit.pack(fill=tk.BOTH, expand=True)
            self.refresh_edit_listbox()
        elif page_name == "test":
            self.frame_test.pack(fill=tk.BOTH, expand=True)

    def back_to_menu(self):
        self.function_frame.pack_forget()
        self.menu_frame.pack(fill=tk.BOTH, expand=True)

    # ==================== 页面1：单词列表 ====================
    def build_list_page(self):
        self.frame_list = ttk.Frame(self.function_frame)
        top_bar = ttk.Frame(self.frame_list)
        top_bar.pack(fill=tk.X, padx=8, pady=5)
        ttk.Button(top_bar, text="← 返回菜单", command=self.back_to_menu).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="单词列表", font=("微软雅黑", 12, "bold")).pack(side=tk.LEFT, padx=15)

        canvas_container = ttk.Frame(self.frame_list)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=5)

        self.list_canvas = tk.Canvas(canvas_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.list_canvas.yview)
        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.list_inner_frame = ttk.Frame(self.list_canvas)
        self.list_canvas_window = self.list_canvas.create_window((0, 0), window=self.list_inner_frame, anchor="nw")
        self.list_inner_frame.bind("<Configure>", self._on_list_frame_configure)
        self.list_canvas.bind("<Configure>", self._on_list_canvas_configure)
        self._bind_mousewheel(self.list_canvas)

        self.list_row_frames = []

    def _on_list_frame_configure(self, event=None):
        self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))

    def _on_list_canvas_configure(self, event):
        self.list_canvas.itemconfig(self.list_canvas_window, width=event.width)

    def _bind_mousewheel(self, widget):
        def _on_mousewheel(event):
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        widget.bind("<MouseWheel>", _on_mousewheel)

    def refresh_list_page(self):
        for frame in self.list_row_frames:
            frame.destroy()
        self.list_row_frames.clear()

        # 按英文单词字母顺序排序
        sorted_words = sorted(self.word_list, key=lambda x: x['english'].lower())

        if not sorted_words:
            empty_label = ttk.Label(self.list_inner_frame, text="📭 暂无单词，请前往「增删改查」页面添加", font=("微软雅黑", 10))
            empty_label.pack(pady=20)
            self.list_row_frames.append(empty_label)
            return

        for idx, word in enumerate(sorted_words):
            row_frame = ttk.Frame(self.list_inner_frame, relief=tk.RIDGE, borderwidth=1)
            row_frame.pack(fill=tk.X, pady=3, padx=2)
            self.list_row_frames.append(row_frame)

            row_frame.columnconfigure(0, weight=0, minsize=100)
            row_frame.columnconfigure(1, weight=1)
            row_frame.columnconfigure(2, weight=0)
            row_frame.columnconfigure(3, weight=0)

            en_label = ttk.Label(row_frame, text=word["english"], font=("微软雅黑", 10, "bold"), foreground="#2c3e50")
            en_label.grid(row=0, column=0, sticky="nw", padx=6, pady=6)

            chn_label = ttk.Label(row_frame, text=word["chinese"], font=("微软雅黑", 9),
                                  wraplength=250, justify=tk.LEFT)
            chn_label.grid(row=0, column=1, sticky="nwse", padx=6, pady=6)
            chn_label.bind("<Configure>", lambda e, lbl=chn_label: self._adjust_wraplength(lbl, e.width))
            chn_label.visible = True

            def make_toggle(label):
                def toggle():
                    if label.visible:
                        label.grid_remove()
                        label.visible = False
                        toggle_btn.config(text="🔼 显示")
                    else:
                        label.grid()
                        label.visible = True
                        toggle_btn.config(text="🔽 隐藏")
                return toggle

            toggle_btn = ttk.Button(row_frame, text="🔽 隐藏", width=7,
                                    command=make_toggle(chn_label))
            toggle_btn.grid(row=0, column=2, sticky="e", padx=4, pady=6)

            detail_btn = ttk.Button(row_frame, text="详情", width=7,
                                    command=lambda w=word: self.show_word_detail(w))
            detail_btn.grid(row=0, column=3, sticky="e", padx=6, pady=6)

        self.list_inner_frame.update_idletasks()
        self._on_list_frame_configure()

    def _adjust_wraplength(self, label, current_width):
        if current_width > 20:
            label.config(wraplength=current_width - 10)

    def show_word_detail(self, word):
        detail_win = tk.Toplevel(self)
        detail_win.title(f"单词详情 - {word['english']}")
        detail_win.geometry("600x550")
        detail_win.resizable(True, True)

        text_area = scrolledtext.ScrolledText(detail_win, wrap=tk.WORD, font=("微软雅黑", 9), padx=8, pady=8)
        text_area.pack(fill=tk.BOTH, expand=True)

        # 格式化中文释义
        formatted_chinese = format_chinese_meaning(word['chinese'])

        # 构建例句文本
        examples_text = ""
        if word.get("examples"):
            for i, ex in enumerate(word["examples"], 1):
                examples_text += f"\n  例句{i}（英）: {ex['en']}\n  例句{i}（中）: {ex['cn']}\n"
        else:
            examples_text = "  无\n"

        info = f"""【单词】{word['english']}

【中文释义】
{formatted_chinese}

【例句】
{examples_text}
【常用短语】
{word.get('phrase', '') or '无'}

【词形变化】
{word.get('word_form', '') or '无'}
"""
        text_area.insert(tk.END, info)
        text_area.config(state=tk.DISABLED)

    # ==================== 页面2：增删改查 ====================
    def build_edit_page(self):
        self.frame_edit = ttk.Frame(self.function_frame)

        top_bar = ttk.Frame(self.frame_edit)
        top_bar.pack(fill=tk.X, padx=8, pady=5)
        ttk.Button(top_bar, text="返回菜单", command=self.back_to_menu).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="增删改查", font=("微软雅黑", 12, "bold")).pack(side=tk.LEFT, padx=15)

        # 搜索栏
        search_frame = ttk.Frame(self.frame_edit)
        search_frame.pack(fill=tk.X, padx=8, pady=5)
        ttk.Label(search_frame, text="🔍 搜索：").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, font=("微软雅黑", 9), width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="搜索", command=self.search_word_edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="重置", command=self.refresh_edit_listbox).pack(side=tk.LEFT, padx=2)

        # 主区域：左侧列表 + 右侧表单
        main_frame = ttk.Frame(self.frame_edit)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=5)

        # 左侧单词列表
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_edit = ttk.Scrollbar(left_frame)
        scroll_edit.pack(side=tk.RIGHT, fill=tk.Y)
        self.edit_listbox = tk.Listbox(left_frame, yscrollcommand=scroll_edit.set, font=("微软雅黑", 9))
        self.edit_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_edit.config(command=self.edit_listbox.yview)
        self.edit_listbox.bind("<<ListboxSelect>>", self.on_edit_select)

        # 右侧编辑表单
        right_frame = ttk.LabelFrame(main_frame, text="单词编辑区")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # 基础字段
        self.var_en = tk.StringVar()
        self.text_cn = scrolledtext.ScrolledText(right_frame, height=3, wrap=tk.WORD, font=("微软雅黑", 9))
        self.text_phrase = scrolledtext.ScrolledText(right_frame, height=2, wrap=tk.WORD, font=("微软雅黑", 9))
        self.text_form = scrolledtext.ScrolledText(right_frame, height=2, wrap=tk.WORD, font=("微软雅黑", 9))

        # 例句框架
        examples_frame = ttk.LabelFrame(right_frame, text="例句（中英文配对）")
        self.examples_container = ttk.Frame(examples_frame)
        self.examples_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.example_rows = []

        btn_add_example = ttk.Button(examples_frame, text="+ 添加新例句", command=self.add_example_row)
        btn_add_example.pack(pady=5)

        # 布局
        row = 0
        ttk.Label(right_frame, text="英文单词 *").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        ttk.Entry(right_frame, textvariable=self.var_en, font=("微软雅黑", 9)).grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1

        ttk.Label(right_frame, text="中文释义").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self.text_cn.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1

        ttk.Label(right_frame, text="例句管理").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        examples_frame.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1

        ttk.Label(right_frame, text="常用短语").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self.text_phrase.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1

        ttk.Label(right_frame, text="词形变化").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self.text_form.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1

        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="➕ 新增", command=self.add_word_edit).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="✏️ 修改", command=self.update_word_edit).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="🗑️ 删除", command=self.del_word_edit).pack(side=tk.LEFT, padx=3)

        right_frame.columnconfigure(1, weight=1)
        self.edit_selected_index = None
        self.refresh_edit_listbox()

    def add_example_row(self, en_text="", cn_text=""):
        row_frame = ttk.Frame(self.examples_container)
        row_frame.pack(fill=tk.X, pady=2)

        en_entry = ttk.Entry(row_frame, font=("微软雅黑", 9))
        en_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        en_entry.insert(0, en_text)

        cn_entry = ttk.Entry(row_frame, font=("微软雅黑", 9))
        cn_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        cn_entry.insert(0, cn_text)

        del_btn = ttk.Button(row_frame, text="✖", width=3,
                             command=lambda f=row_frame: self.remove_example_row(f))
        del_btn.pack(side=tk.LEFT)

        self.example_rows.append({"frame": row_frame, "en": en_entry, "cn": cn_entry})

    def remove_example_row(self, frame):
        for i, row in enumerate(self.example_rows):
            if row["frame"] == frame:
                row["frame"].destroy()
                del self.example_rows[i]
                break

    def clear_example_rows(self):
        for row in self.example_rows:
            row["frame"].destroy()
        self.example_rows.clear()

    def load_examples_to_ui(self, examples_list):
        self.clear_example_rows()
        for ex in examples_list:
            self.add_example_row(ex.get("en", ""), ex.get("cn", ""))

    def get_examples_from_ui(self):
        return [{"en": row["en"].get().strip(), "cn": row["cn"].get().strip()}
                for row in self.example_rows if row["en"].get().strip() or row["cn"].get().strip()]

    def refresh_edit_listbox(self):
        self.edit_listbox.delete(0, tk.END)
        # 按字母顺序排序显示
        sorted_words = sorted(self.word_list, key=lambda x: x['english'].lower())
        for idx, w in enumerate(sorted_words):
            self.edit_listbox.insert(tk.END, f"{idx+1}. {w['english']}")
        self.clear_edit_form()
        self.edit_selected_index = None
        # 保存排序后的列表用于索引映射
        self.sorted_word_list = sorted_words

    def search_word_edit(self):
        keyword = self.search_entry.get().strip().lower()
        self.edit_listbox.delete(0, tk.END)
        filtered = [w for w in self.word_list if keyword in w['english'].lower() or keyword in w['chinese']]
        filtered_sorted = sorted(filtered, key=lambda x: x['english'].lower())
        for idx, w in enumerate(filtered_sorted):
            self.edit_listbox.insert(tk.END, f"{idx+1}. {w['english']}")
        self.sorted_word_list = filtered_sorted

    def on_edit_select(self, event):
        selection = self.edit_listbox.curselection()
        if not selection:
            return
        selected_text = self.edit_listbox.get(selection[0])
        try:
            idx = int(selected_text.split(".")[0]) - 1
            if 0 <= idx < len(self.sorted_word_list):
                selected_word = self.sorted_word_list[idx]
                original_idx = self.word_list.index(selected_word)
                self.edit_selected_index = original_idx

                w = selected_word
                self.var_en.set(w['english'])
                self.text_cn.delete(1.0, tk.END)
                self.text_cn.insert(tk.END, w['chinese'])
                self.text_phrase.delete(1.0, tk.END)
                self.text_phrase.insert(tk.END, w.get('phrase', ''))
                self.text_form.delete(1.0, tk.END)
                self.text_form.insert(tk.END, w.get('word_form', ''))
                self.load_examples_to_ui(w.get("examples", []))
        except Exception:
            pass

    def clear_edit_form(self):
        self.var_en.set("")
        self.text_cn.delete(1.0, tk.END)
        self.text_phrase.delete(1.0, tk.END)
        self.text_form.delete(1.0, tk.END)
        self.clear_example_rows()

    def get_edit_form_data(self):
        return {
            "english": self.var_en.get().strip(),
            "chinese": self.text_cn.get(1.0, tk.END).strip(),
            "examples": self.get_examples_from_ui(),
            "phrase": self.text_phrase.get(1.0, tk.END).strip(),
            "word_form": self.text_form.get(1.0, tk.END).strip()
        }

    def add_word_edit(self):
        data = self.get_edit_form_data()
        if not data["english"]:
            messagebox.showwarning("警告", "英文单词不能为空")
            return
        self.word_list.append(data)
        self._after_data_change()

    def update_word_edit(self):
        if self.edit_selected_index is None:
            messagebox.showwarning("提示", "请先选中要修改的单词")
            return
        data = self.get_edit_form_data()
        if not data["english"]:
            messagebox.showwarning("警告", "英文单词不能为空")
            return
        self.word_list[self.edit_selected_index] = data
        self._after_data_change()

    def del_word_edit(self):
        if self.edit_selected_index is None:
            messagebox.showwarning("提示", "请先选中要删除的单词")
            return
        confirm = messagebox.askyesno("确认删除", f"确定要删除单词「{self.word_list[self.edit_selected_index]['english']}」吗？")
        if confirm:
            del self.word_list[self.edit_selected_index]
            self._after_data_change()

    def _after_data_change(self):
        save_words(self.word_list)
        self.refresh_edit_listbox()
        self.refresh_list_page()
        messagebox.showinfo("成功", "操作完成")

    # ==================== 页面3：卡片自测 ====================
    def build_test_page(self):
        self.frame_test = ttk.Frame(self.function_frame)

        top_bar = ttk.Frame(self.frame_test)
        top_bar.pack(fill=tk.X, padx=8, pady=5)
        ttk.Button(top_bar, text="← 返回菜单", command=self.back_to_menu).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="卡片自测", font=("微软雅黑", 12, "bold")).pack(side=tk.LEFT, padx=15)

        control_frame = ttk.Frame(self.frame_test)
        control_frame.pack(fill=tk.X, padx=8, pady=5)
        self.test_start_btn = ttk.Button(control_frame, text="🎲 开始随机自测", command=self.start_test)
        self.test_start_btn.pack(side=tk.LEFT, padx=5)
        self.test_status_label = ttk.Label(control_frame, text="未开始", foreground="gray")
        self.test_status_label.pack(side=tk.LEFT, padx=15)

        card_container = ttk.Frame(self.frame_test)
        card_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.card_label = tk.Label(card_container, text="点击【开始随机自测】", font=("微软雅黑", 12),
                                   bg="#f0f8ff", relief=tk.RIDGE, bd=2, wraplength=600, justify=tk.LEFT)
        self.card_label.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        self.card_label.bind("<Button-1>", self.flip_card)

        btn_frame = ttk.Frame(self.frame_test)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="✅ 认识", command=self.know_word, width=10).pack(side=tk.LEFT, padx=15)
        ttk.Button(btn_frame, text="❌ 不认识", command=self.unknow_word, width=10).pack(side=tk.LEFT, padx=15)

        self.test_word_pool = []
        self.current_test_idx = 0
        self.card_flipped = False

    def start_test(self):
        if not self.word_list:
            messagebox.showwarning("提示", "单词本为空，请先添加单词")
            return
        self.test_word_pool = self.word_list.copy()
        random.shuffle(self.test_word_pool)
        self.current_test_idx = 0
        self.card_flipped = False
        self.show_test_card()
        self.test_status_label.config(text=f"进度: 0 / {len(self.test_word_pool)}")

    def show_test_card(self):
        if self.current_test_idx >= len(self.test_word_pool):
            self.card_label.config(text="🎉 恭喜！本轮自测完成！\n点击「开始随机自测」可重新开始")
            self.test_status_label.config(text="自测结束")
            return
        w = self.test_word_pool[self.current_test_idx]
        if not self.card_flipped:
            self.card_label.config(text=f"📖 {w['english']}\n\n(点击卡片查看详情)", font=("微软雅黑", 14, "bold"))
        else:
            examples_str = ""
            if w.get("examples"):
                for i, ex in enumerate(w["examples"], 1):
                    examples_str += f"\n例句{i}: {ex['en']}\n    {ex['cn']}"
            else:
                examples_str = "无"
            detail = f"""【单词】{w['english']}

【释义】{w['chinese']}

【例句】{examples_str}

【短语】{w.get('phrase', '无')}
【词形】{w.get('word_form', '无')}"""
            self.card_label.config(text=detail, font=("微软雅黑", 10), justify=tk.LEFT)

    def flip_card(self, event=None):
        if self.current_test_idx >= len(self.test_word_pool) or not self.test_word_pool:
            return
        self.card_flipped = not self.card_flipped
        self.show_test_card()

    def know_word(self):
        if self.current_test_idx >= len(self.test_word_pool):
            return
        self.current_test_idx += 1
        self.card_flipped = False
        self.show_test_card()
        self.test_status_label.config(text=f"进度: {self.current_test_idx} / {len(self.test_word_pool)}")

    def unknow_word(self):
        if self.current_test_idx >= len(self.test_word_pool):
            return
        if not self.card_flipped:
            self.card_flipped = True
            self.show_test_card()


# ===================== 启动 =====================
if __name__ == "__main__":
    app = WordBookApp()
    app.mainloop()