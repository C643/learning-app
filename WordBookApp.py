import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


# ===================== 数据库管理类 =====================
class Database:
    DB_FILE = "data.json"

    @classmethod
    def init(cls):
        if not os.path.exists(cls.DB_FILE):
            with open(cls.DB_FILE, "w", encoding="utf-8") as f:
                json.dump({"words": [], "sentences": []}, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_data(cls):
        try:
            with open(cls.DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"words": [], "sentences": []}

    @classmethod
    def save_data(cls, data):
        with open(cls.DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_words(cls):
        data = cls.load_data()
        return data.get("words", [])

    @classmethod
    def save_words(cls, words):
        data = cls.load_data()
        data["words"] = words
        cls.save_data(data)

    @classmethod
    def load_sentences(cls):
        data = cls.load_data()
        return data.get("sentences", [])

    @classmethod
    def save_sentences(cls, sentences):
        data = cls.load_data()
        data["sentences"] = sentences
        cls.save_data(data)


# ===================== 工具函数 =====================
def create_scrollable_container(parent, bg=None):
    """创建一个带滚动条的容器，返回 (canvas, inner_frame)"""
    canvas = tk.Canvas(parent, highlightthickness=0, bg=bg) if bg else tk.Canvas(parent, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    inner = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.create_window((0, 0), window=inner, anchor="nw"), width=e.width))

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<MouseWheel>", _on_mousewheel)

    return canvas, inner


# ===================== 主程序 =====================
class WordBookApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("英语学习助手")
        self.geometry("600x500")
        self.minsize(500, 500)

        # 加载数据
        self.word_list = Database.load_words()
        self.sentence_list = Database.load_sentences()

        # 主容器
        self.menu_frame = ttk.Frame(self)
        self.function_frame = ttk.Frame(self)

        self.menu_frame.pack(fill=tk.BOTH, expand=True)
        self.function_frame.pack(fill=tk.BOTH, expand=True)
        self.function_frame.pack_forget()

        # 构建所有页面
        self.build_menu()
        self.build_word_list_page()
        self.build_word_edit_page()
        self.build_sentence_list_page()
        self.build_sentence_edit_page()

    # ========== 菜单：四个卡片，2行2列 ==========
    def build_menu(self):
        center_frame = ttk.Frame(self.menu_frame)
        center_frame.pack(expand=True)

        card_width, card_height = 180, 180
        padding = 22

        def make_card(parent, row, col, bg, icon, text, page_name):
            card = tk.Canvas(parent, width=card_width, height=card_height, bg=bg, highlightthickness=0)
            card.grid(row=row, column=col, padx=padding, pady=padding)
            card.create_text(card_width // 2, card_height // 2 - 20, text=icon, font=("Segoe UI", 44), fill="white")
            card.create_text(card_width // 2, card_height // 2 + 30, text=text, font=("微软雅黑", 12, "bold"), fill="white")
            card.bind("<Button-1>", lambda e, p=page_name: self.show_function_page(p))
            card.bind("<Enter>", lambda e, c=card, bg=bg: c.config(bg=self._darken_color(bg)))
            card.bind("<Leave>", lambda e, c=card, bg=bg: c.config(bg=bg))
            return card

        # 第一行
        make_card(center_frame, 0, 0, "#3498db", "📖", "单词列表", "word_list")
        make_card(center_frame, 0, 1, "#2ecc71", "✏️", "单词增删改查", "word_edit")
        # 第二行
        make_card(center_frame, 1, 0, "#9b59b6", "📝", "句子库", "sentence_list")
        make_card(center_frame, 1, 1, "#1abc9c", "✍️", "句子增删改查", "sentence_edit")

    @staticmethod
    def _darken_color(hex_color):
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
        darker = tuple(max(0, int(c * 0.8)) for c in rgb)
        return f"#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}"

    def show_function_page(self, page_name):
        self.menu_frame.pack_forget()
        self.function_frame.pack(fill=tk.BOTH, expand=True)

        self.frame_word_list.pack_forget()
        self.frame_word_edit.pack_forget()
        self.frame_sentence_list.pack_forget()
        self.frame_sentence_edit.pack_forget()

        if page_name == "word_list":
            self.frame_word_list.pack(fill=tk.BOTH, expand=True)
            self.refresh_word_list_page()
        elif page_name == "word_edit":
            self.frame_word_edit.pack(fill=tk.BOTH, expand=True)
            self.refresh_word_edit_listbox()
        elif page_name == "sentence_list":
            self.frame_sentence_list.pack(fill=tk.BOTH, expand=True)
            self.refresh_sentence_list_page()
        elif page_name == "sentence_edit":
            self.frame_sentence_edit.pack(fill=tk.BOTH, expand=True)
            self.refresh_sentence_edit_listbox()

    def back_to_menu(self):
        self.function_frame.pack_forget()
        self.menu_frame.pack(fill=tk.BOTH, expand=True)

    # ==================== 单词列表页面 ====================
    def build_word_list_page(self):
        self.frame_word_list = ttk.Frame(self.function_frame)
        top_bar = ttk.Frame(self.frame_word_list)
        top_bar.pack(fill=tk.X, padx=8, pady=5)
        ttk.Button(top_bar, text="← 返回菜单", command=self.back_to_menu).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="单词列表", font=("微软雅黑", 12, "bold")).pack(side=tk.LEFT, padx=15)

        canvas_container = ttk.Frame(self.frame_word_list)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=5)

        self.word_list_canvas, self.word_list_inner = create_scrollable_container(canvas_container)
        self.word_list_rows = []  # 存储 (row_frame, detail_frame, word, detail_btn)

    def refresh_word_list_page(self):
        for child in self.word_list_inner.winfo_children():
            child.destroy()
        self.word_list_rows.clear()

        sorted_words = sorted(self.word_list, key=lambda x: x['english'].lower())
        if not sorted_words:
            empty_label = ttk.Label(self.word_list_inner, text="📭 暂无单词，请前往「单词增删改查」添加", font=("微软雅黑", 10))
            empty_label.pack(pady=20)
            self.word_list_rows.append((empty_label, None, None, None))
            return

        for word in sorted_words:
            # 主行 frame
            row_frame = ttk.Frame(self.word_list_inner, relief=tk.RIDGE, borderwidth=1)
            row_frame.pack(fill=tk.X, pady=2, padx=2)

            # 英文标签
            en_label = ttk.Label(row_frame, text=word["english"], font=("微软雅黑", 12, "bold"), foreground="#2c3e50")
            en_label.grid(row=0, column=0, sticky="w", padx=6, pady=4)

            # 中文标签
            chn_label = ttk.Label(row_frame, text=word["chinese"], font=("微软雅黑", 10), wraplength=500, justify=tk.LEFT)
            chn_label.grid(row=1, column=0, sticky="w", padx=6, pady=2)

            # 按钮区域
            btn_frame = ttk.Frame(row_frame)
            btn_frame.grid(row=0, column=1, rowspan=2, sticky="ne", padx=6, pady=4)
            row_frame.columnconfigure(0, weight=1)

            # 隐藏/显示中文按钮
            toggle_btn = ttk.Button(btn_frame, text="隐藏", command=lambda l=chn_label, b=None: self._toggle_label_visibility(l, b))
            toggle_btn.pack(side=tk.LEFT, padx=2)

            # 详情按钮
            detail_btn = ttk.Button(btn_frame, text="详情")
            detail_btn.pack(side=tk.LEFT, padx=2)

            # 详情 frame
            detail_frame = tk.Frame(self.word_list_inner, relief=tk.RIDGE, bd=1, bg="#f9f9f9")
            detail_frame.pack(fill=tk.X, pady=(0, 2), padx=2)
            detail_frame.pack_forget()

            # 保存行数据
            self.word_list_rows.append((row_frame, detail_frame, word, detail_btn))

            # 绑定详情按钮事件
            detail_btn.config(command=lambda w=word, rf=row_frame, df=detail_frame, btn=detail_btn: self._toggle_word_detail(w, rf, df, btn))

    def _toggle_label_visibility(self, label, btn):
        """隐藏/显示中文释义"""
        if label.winfo_ismapped():
            label.grid_remove()
            btn.config(text="显示")
        else:
            label.grid()
            btn.config(text="隐藏")

    def _toggle_word_detail(self, word, row_frame, detail_frame, detail_btn):
        """展开/收起单词详情"""
        for rf, df, w, btn in self.word_list_rows:
            if rf == row_frame and w == word:
                if df.winfo_ismapped():
                    df.pack_forget()
                    btn.config(text="详情")
                else:
                    self._update_word_detail_frame(df, word)
                    df.pack(fill=tk.X, pady=(0, 2), padx=2, after=rf)
                    btn.config(text="收起")
                break

    def _update_word_detail_frame(self, frame, word):
        """刷新单词详情 frame 的内容（例句、补充）"""
        for child in frame.winfo_children():
            child.destroy()

        # 例句部分
        examples = word.get('examples', [])
        if examples:
            ex_frame = ttk.Frame(frame)
            ex_frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(ex_frame, text="【例句】", font=("微软雅黑", 9, "bold"), background="#f9f9f9").pack(anchor=tk.W, pady=(2,0))
            ex_text = ""
            for i, ex in enumerate(examples, 1):
                ex_text += f"{i}. {ex['en']}\n    {ex['cn']}\n"
            ex_label = ttk.Label(ex_frame, text=ex_text.strip(), font=("微软雅黑", 9), justify=tk.LEFT, wraplength=550, background="#f9f9f9")
            ex_label.pack(fill=tk.X, padx=5, pady=2)

        # 补充部分
        supplement = word.get('supplement', '').strip()
        if supplement:
            sup_frame = ttk.Frame(frame)
            sup_frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(sup_frame, text="【补充】", font=("微软雅黑", 9, "bold"), background="#f9f9f9").pack(anchor=tk.W, pady=(2,0))
            sup_label = ttk.Label(sup_frame, text=supplement, font=("微软雅黑", 9), justify=tk.LEFT, wraplength=550, background="#f9f9f9")
            sup_label.pack(fill=tk.X, padx=5, pady=2)

        if not examples and not supplement:
            empty_label = ttk.Label(frame, text="无更多信息", font=("微软雅黑", 9), foreground="gray", background="#f9f9f9")
            empty_label.pack(pady=4)

    # ==================== 单词增删改查页面 ====================
    def build_word_edit_page(self):
        self.frame_word_edit = ttk.Frame(self.function_frame)
        top_bar = ttk.Frame(self.frame_word_edit)
        top_bar.pack(fill=tk.X, padx=8, pady=5)
        ttk.Button(top_bar, text="返回菜单", command=self.back_to_menu).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="单词增删改查", font=("微软雅黑", 12, "bold")).pack(side=tk.LEFT, padx=15)

        search_frame = ttk.Frame(self.frame_word_edit)
        search_frame.pack(fill=tk.X, padx=8, pady=5)
        ttk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)
        self.word_search_entry = ttk.Entry(search_frame, width=20)
        self.word_search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="搜索", command=self.search_word_edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="重置", command=self.refresh_word_edit_listbox).pack(side=tk.LEFT, padx=2)

        main_frame = ttk.Frame(self.frame_word_edit)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=5)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_edit = ttk.Scrollbar(left_frame)
        scroll_edit.pack(side=tk.RIGHT, fill=tk.Y)
        self.word_edit_listbox = tk.Listbox(left_frame, yscrollcommand=scroll_edit.set, font=("微软雅黑", 9))
        self.word_edit_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_edit.config(command=self.word_edit_listbox.yview)
        self.word_edit_listbox.bind("<<ListboxSelect>>", self.on_word_edit_select)

        right_frame = ttk.LabelFrame(main_frame, text="单词编辑区")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        canvas, inner_frame = create_scrollable_container(right_frame)

        self.var_en = tk.StringVar()
        self.text_cn = scrolledtext.ScrolledText(inner_frame, height=3, wrap=tk.WORD)
        self.text_supplement = scrolledtext.ScrolledText(inner_frame, height=3, wrap=tk.WORD)

        # 例句管理
        examples_frame = ttk.LabelFrame(inner_frame, text="例句")
        self.examples_container = ttk.Frame(examples_frame)
        self.examples_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.example_rows = []
        ttk.Button(examples_frame, text="+ 添加例句", command=self.add_example_row).pack(pady=5)

        # 布局
        row = 0
        ttk.Label(inner_frame, text="英文单词 *").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        ttk.Entry(inner_frame, textvariable=self.var_en).grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1
        ttk.Label(inner_frame, text="中文释义 *").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self.text_cn.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1
        ttk.Label(inner_frame, text="例句管理").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        examples_frame.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1
        ttk.Label(inner_frame, text="补充").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self.text_supplement.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1

        btn_frame = ttk.Frame(inner_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="新增", command=self.add_word_edit).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="修改", command=self.update_word_edit).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="删除", command=self.del_word_edit).pack(side=tk.LEFT, padx=3)

        inner_frame.columnconfigure(1, weight=1)

        self.word_edit_selected_index = None
        self.sorted_word_list = []
        self.refresh_word_edit_listbox()

    def add_example_row(self, en="", cn=""):
        row_frame = ttk.Frame(self.examples_container)
        row_frame.pack(fill=tk.X, pady=2)
        en_entry = ttk.Entry(row_frame)
        en_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        en_entry.insert(0, en)
        cn_entry = ttk.Entry(row_frame)
        cn_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        cn_entry.insert(0, cn)
        del_btn = ttk.Button(row_frame, text="✖", width=3, command=lambda: self._remove_example_row(row_frame))
        del_btn.pack(side=tk.LEFT)
        self.example_rows.append({"frame": row_frame, "en": en_entry, "cn": cn_entry})

    def _remove_example_row(self, frame):
        for i, row in enumerate(self.example_rows):
            if row["frame"] == frame:
                row["frame"].destroy()
                del self.example_rows[i]
                break

    def clear_example_rows(self):
        for row in self.example_rows:
            row["frame"].destroy()
        self.example_rows.clear()

    def load_examples_to_ui(self, examples):
        self.clear_example_rows()
        for ex in examples:
            self.add_example_row(ex.get("en", ""), ex.get("cn", ""))

    def get_examples_from_ui(self):
        return [{"en": row["en"].get().strip(), "cn": row["cn"].get().strip()} for row in self.example_rows if
                row["en"].get().strip() or row["cn"].get().strip()]

    def refresh_word_edit_listbox(self):
        self.word_edit_listbox.delete(0, tk.END)
        self.sorted_word_list = sorted(self.word_list, key=lambda x: x['english'].lower())
        for i, w in enumerate(self.sorted_word_list):
            self.word_edit_listbox.insert(tk.END, f"{i + 1}. {w['english']}")
        self.word_edit_selected_index = None
        self._clear_word_edit_form()

    def search_word_edit(self):
        keyword = self.word_search_entry.get().strip().lower()
        self.word_edit_listbox.delete(0, tk.END)
        filtered = [w for w in self.word_list if keyword in w['english'].lower() or keyword in w['chinese']]
        self.sorted_word_list = sorted(filtered, key=lambda x: x['english'].lower())
        for i, w in enumerate(self.sorted_word_list):
            self.word_edit_listbox.insert(tk.END, f"{i + 1}. {w['english']}")

    def on_word_edit_select(self, event):
        selection = self.word_edit_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self.sorted_word_list):
            word = self.sorted_word_list[idx]
            original_idx = self.word_list.index(word)
            self.word_edit_selected_index = original_idx
            self.var_en.set(word['english'])
            self.text_cn.delete(1.0, tk.END)
            self.text_cn.insert(tk.END, word['chinese'])
            self.text_supplement.delete(1.0, tk.END)
            self.text_supplement.insert(tk.END, word.get('supplement', ''))
            self.load_examples_to_ui(word.get("examples", []))

    def _clear_word_edit_form(self):
        self.var_en.set("")
        self.text_cn.delete(1.0, tk.END)
        self.text_supplement.delete(1.0, tk.END)
        self.clear_example_rows()

    def get_word_edit_data(self):
        return {
            "english": self.var_en.get().strip(),
            "chinese": self.text_cn.get(1.0, tk.END).strip(),
            "examples": self.get_examples_from_ui(),
            "supplement": self.text_supplement.get(1.0, tk.END).strip()
        }

    def add_word_edit(self):
        data = self.get_word_edit_data()
        if not data["english"]:
            messagebox.showwarning("警告", "英文单词不能为空")
            return
        if not data["chinese"]:
            messagebox.showwarning("警告", "中文释义不能为空")
            return
        self.word_list.append(data)
        self._after_word_change()

    def update_word_edit(self):
        if self.word_edit_selected_index is None:
            messagebox.showwarning("提示", "请先选中单词")
            return
        data = self.get_word_edit_data()
        if not data["english"]:
            messagebox.showwarning("警告", "英文单词不能为空")
            return
        if not data["chinese"]:
            messagebox.showwarning("警告", "中文释义不能为空")
            return
        self.word_list[self.word_edit_selected_index] = data
        self._after_word_change()

    def del_word_edit(self):
        if self.word_edit_selected_index is None:
            messagebox.showwarning("提示", "请先选中单词")
            return
        confirm = messagebox.askyesno("确认", f"删除「{self.word_list[self.word_edit_selected_index]['english']}」？")
        if confirm:
            del self.word_list[self.word_edit_selected_index]
            self._after_word_change()

    def _after_word_change(self):
        Database.save_words(self.word_list)
        self.refresh_word_edit_listbox()
        self.refresh_word_list_page()
        messagebox.showinfo("成功", "操作完成")

    # ==================== 句子库页面 ====================
    def build_sentence_list_page(self):
        self.frame_sentence_list = ttk.Frame(self.function_frame)
        top_bar = ttk.Frame(self.frame_sentence_list)
        top_bar.pack(fill=tk.X, padx=8, pady=5)
        ttk.Button(top_bar, text="← 返回菜单", command=self.back_to_menu).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="句子库", font=("微软雅黑", 12, "bold")).pack(side=tk.LEFT, padx=15)

        canvas_container = ttk.Frame(self.frame_sentence_list)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=5)

        self.sentence_list_canvas, self.sentence_list_inner = create_scrollable_container(canvas_container)
        self.sentence_list_rows = []

    def refresh_sentence_list_page(self):
        for row_frame, detail_frame, _, _ in self.sentence_list_rows:
            row_frame.destroy()
            if detail_frame:
                detail_frame.destroy()
        self.sentence_list_rows.clear()

        sentences = Database.load_sentences()
        if not sentences:
            empty_label = ttk.Label(self.sentence_list_inner, text="📭 暂无句子，请前往「句子增删改查」添加", font=("微软雅黑", 10))
            empty_label.pack(pady=20)
            self.sentence_list_rows.append((empty_label, None, None, None))
            return

        for sent in sentences:
            row_frame = ttk.Frame(self.sentence_list_inner, relief=tk.RIDGE, borderwidth=1)
            row_frame.pack(fill=tk.X, pady=2, padx=2)

            en_label = ttk.Label(row_frame, text=sent["english"], font=("微软雅黑", 12, "bold"), foreground="#2c3e50",
                                 wraplength=500, justify=tk.LEFT)
            en_label.grid(row=0, column=0, sticky="w", padx=6, pady=2)
            cn_label = ttk.Label(row_frame, text=sent["chinese"], font=("微软雅黑", 10), wraplength=500,
                                 justify=tk.LEFT)
            cn_label.grid(row=1, column=0, sticky="w", padx=6, pady=2)

            btn_frame = ttk.Frame(row_frame)
            btn_frame.grid(row=0, column=1, rowspan=2, sticky="ne", padx=6, pady=4)
            row_frame.columnconfigure(0, weight=1)

            detail_btn = ttk.Button(btn_frame, text="详情", command=lambda s=sent, rf=row_frame: self._toggle_sentence_detail(s, rf))
            detail_btn.pack()

            detail_frame = tk.Frame(self.sentence_list_inner, relief=tk.RIDGE, bd=1, bg="#f9f9f9")
            detail_frame.pack(fill=tk.X, pady=(0, 2), padx=2)
            detail_frame.pack_forget()

            self.sentence_list_rows.append((row_frame, detail_frame, sent, detail_btn))

    def _toggle_sentence_detail(self, sentence, row_frame):
        for rf, df, s, btn in self.sentence_list_rows:
            if rf == row_frame and s == sentence:
                if df.winfo_ismapped():
                    df.pack_forget()
                    btn.config(text="详情")
                else:
                    self._update_sentence_detail_frame(df, sentence)
                    df.pack(fill=tk.X, pady=(0, 2), padx=2, after=rf)
                    btn.config(text="收起")
                break

    def _update_sentence_detail_frame(self, frame, sentence):
        for child in frame.winfo_children():
            child.destroy()
        kp = sentence.get('knowledge_points', '').strip()
        if kp:
            label = ttk.Label(frame, text=f"【知识点】\n{kp}", font=("微软雅黑", 9), justify=tk.LEFT,
                              wraplength=550, background="#f9f9f9")
            label.pack(fill=tk.X, padx=5, pady=4)
        else:
            empty_label = ttk.Label(frame, text="无知识点", font=("微软雅黑", 9), foreground="gray", background="#f9f9f9")
            empty_label.pack(pady=4)

    # ==================== 句子增删改查页面 ====================
    def build_sentence_edit_page(self):
        self.frame_sentence_edit = ttk.Frame(self.function_frame)
        top_bar = ttk.Frame(self.frame_sentence_edit)
        top_bar.pack(fill=tk.X, padx=8, pady=5)
        ttk.Button(top_bar, text="返回菜单", command=self.back_to_menu).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="句子增删改查", font=("微软雅黑", 12, "bold")).pack(side=tk.LEFT, padx=15)

        search_frame = ttk.Frame(self.frame_sentence_edit)
        search_frame.pack(fill=tk.X, padx=8, pady=5)
        ttk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)
        self.sentence_search_entry = ttk.Entry(search_frame, width=20)
        self.sentence_search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="搜索", command=self.search_sentence_edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="重置", command=self.refresh_sentence_edit_listbox).pack(side=tk.LEFT, padx=2)

        main_frame = ttk.Frame(self.frame_sentence_edit)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=5)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_edit = ttk.Scrollbar(left_frame)
        scroll_edit.pack(side=tk.RIGHT, fill=tk.Y)
        self.sentence_edit_listbox = tk.Listbox(left_frame, yscrollcommand=scroll_edit.set, font=("微软雅黑", 9))
        self.sentence_edit_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_edit.config(command=self.sentence_edit_listbox.yview)
        self.sentence_edit_listbox.bind("<<ListboxSelect>>", self.on_sentence_edit_select)

        right_frame = ttk.LabelFrame(main_frame, text="句子编辑区")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        canvas, inner_frame = create_scrollable_container(right_frame)

        self.sentence_en_text = scrolledtext.ScrolledText(inner_frame, height=4, wrap=tk.WORD, font=("微软雅黑", 9))
        self.sentence_cn_text = scrolledtext.ScrolledText(inner_frame, height=3, wrap=tk.WORD, font=("微软雅黑", 9))
        self.sentence_kp_text = scrolledtext.ScrolledText(inner_frame, height=6, wrap=tk.WORD, font=("微软雅黑", 9))

        row = 0
        ttk.Label(inner_frame, text="英文句子 *").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self.sentence_en_text.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1
        ttk.Label(inner_frame, text="中文翻译").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self.sentence_cn_text.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1
        ttk.Label(inner_frame, text="知识点/短语").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self.sentence_kp_text.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
        row += 1

        btn_frame = ttk.Frame(inner_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="新增", command=self.add_sentence_edit).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="修改", command=self.update_sentence_edit).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="删除", command=self.del_sentence_edit).pack(side=tk.LEFT, padx=3)

        inner_frame.columnconfigure(1, weight=1)

        self.sentence_edit_selected_id = None
        self.sorted_sentence_list = []
        self.refresh_sentence_edit_listbox()

    def refresh_sentence_edit_listbox(self):
        self.sentence_edit_listbox.delete(0, tk.END)
        self.sorted_sentence_list = sorted(Database.load_sentences(), key=lambda x: x['english'].lower())
        for i, s in enumerate(self.sorted_sentence_list):
            self.sentence_edit_listbox.insert(tk.END, f"{i + 1}. {s['english'][:60]}...")
        self.sentence_edit_selected_id = None
        self._clear_sentence_edit_form()

    def search_sentence_edit(self):
        keyword = self.sentence_search_entry.get().strip().lower()
        self.sentence_edit_listbox.delete(0, tk.END)
        all_sentences = Database.load_sentences()
        filtered = [s for s in all_sentences if keyword in s['english'].lower() or keyword in s['chinese'].lower()]
        self.sorted_sentence_list = sorted(filtered, key=lambda x: x['english'].lower())
        for i, s in enumerate(self.sorted_sentence_list):
            self.sentence_edit_listbox.insert(tk.END, f"{i + 1}. {s['english'][:60]}...")

    def on_sentence_edit_select(self, event):
        selection = self.sentence_edit_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self.sorted_sentence_list):
            sent = self.sorted_sentence_list[idx]
            self.sentence_edit_selected_id = sent.get("id")
            self.sentence_en_text.delete(1.0, tk.END)
            self.sentence_en_text.insert(tk.END, sent['english'])
            self.sentence_cn_text.delete(1.0, tk.END)
            self.sentence_cn_text.insert(tk.END, sent['chinese'])
            self.sentence_kp_text.delete(1.0, tk.END)
            self.sentence_kp_text.insert(tk.END, sent.get('knowledge_points', ''))

    def _clear_sentence_edit_form(self):
        self.sentence_en_text.delete(1.0, tk.END)
        self.sentence_cn_text.delete(1.0, tk.END)
        self.sentence_kp_text.delete(1.0, tk.END)

    def _get_next_sentence_id(self):
        sentences = Database.load_sentences()
        if not sentences:
            return 1
        return max(s.get("id", 0) for s in sentences) + 1

    def add_sentence_edit(self):
        en = self.sentence_en_text.get(1.0, tk.END).strip()
        if not en:
            messagebox.showwarning("警告", "英文句子不能为空")
            return
        new_sentence = {
            "id": self._get_next_sentence_id(),
            "english": en,
            "chinese": self.sentence_cn_text.get(1.0, tk.END).strip(),
            "knowledge_points": self.sentence_kp_text.get(1.0, tk.END).strip()
        }
        sentences = Database.load_sentences()
        sentences.append(new_sentence)
        Database.save_sentences(sentences)
        self._after_sentence_change()

    def update_sentence_edit(self):
        if self.sentence_edit_selected_id is None:
            messagebox.showwarning("提示", "请先选中句子")
            return
        en = self.sentence_en_text.get(1.0, tk.END).strip()
        if not en:
            messagebox.showwarning("警告", "英文句子不能为空")
            return
        sentences = Database.load_sentences()
        for i, s in enumerate(sentences):
            if s.get("id") == self.sentence_edit_selected_id:
                sentences[i] = {
                    "id": self.sentence_edit_selected_id,
                    "english": en,
                    "chinese": self.sentence_cn_text.get(1.0, tk.END).strip(),
                    "knowledge_points": self.sentence_kp_text.get(1.0, tk.END).strip()
                }
                break
        Database.save_sentences(sentences)
        self._after_sentence_change()

    def del_sentence_edit(self):
        if self.sentence_edit_selected_id is None:
            messagebox.showwarning("提示", "请先选中句子")
            return
        confirm = messagebox.askyesno("确认", "确定删除这个句子吗？")
        if confirm:
            sentences = Database.load_sentences()
            sentences = [s for s in sentences if s.get("id") != self.sentence_edit_selected_id]
            Database.save_sentences(sentences)
            self._after_sentence_change()

    def _after_sentence_change(self):
        self.refresh_sentence_edit_listbox()
        self.refresh_sentence_list_page()
        messagebox.showinfo("成功", "操作完成")


if __name__ == "__main__":
    Database.init()
    app = WordBookApp()
    app.mainloop()