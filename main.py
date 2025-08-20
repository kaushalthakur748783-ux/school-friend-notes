# main.py
import os, json, random, glob
from datetime import datetime

# ---- Kivy ----
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.core.text import LabelBase


from kivy.core.window import Window

class StudentApp(App):
    def build(self):
        self.icon = "logo.png"   # ✅ App का Logo सेट किया
        return sms



# ---- Voice & TTS ----
from plyer import sms
import speech_recognition as sr
import pyttsx3

# ---- Optional PDF export (reportlab) ----
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.units import cm
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# =============== Hindi font register (auto-detect) ===============
for _p in [
    "NotoSansDevanagari-Regular.ttf",
    "NotoSansDevanagari-VariableFont_wdth,wght.ttf",
]:
    if os.path.exists(_p):
        LabelBase.register(name="HindiFont", fn_regular=_p)
        break

# =============== Storage ===============
NOTES_FILE = "notes.json"
IMAGES_DIR = "pictures"
os.makedirs(IMAGES_DIR, exist_ok=True)

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

# =============== Quotes ===============
QUOTES = [
    ("Believe in yourself and keep going.", "खुद पर विश्वास रखो और चलते रहो।"),
    ("Small progress each day adds up to big results.", "हर दिन की छोटी प्रगति बड़े नतीजों में बदलती है।"),
    ("The secret to getting ahead is getting started.", "आगे बढ़ने का रहस्य है—शुरुआत करना।"),
    ("Discipline beats motivation in the long run.", "लंबे समय में अनुशासन प्रेरणा से आगे है।"),
    ("Focus on improvement, not perfection.", "पूर्णता नहीं, सुधार पर ध्यान दो।"),
    ("Make your future proud of your present.", "ऐसा काम करो कि भविष्य आज पर गर्व करे।"),
    ("Study smart, rest well, repeat.", "स्मार्ट पढ़ो, अच्छा आराम करो, दोहराओ।"),
]

# =============== Helpers ===============
def list_all_images():
    exts = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")
    files = []
    for e in exts:
        files += glob.glob(e)
        files += glob.glob(os.path.join(IMAGES_DIR, e))
    seen, uniq = set(), []
    for f in files:
        fn = os.path.abspath(f)
        if fn not in seen:
            seen.add(fn)
            uniq.append(fn)
    return uniq

def show_info(title, message):
    box = BoxLayout(orientation="vertical", padding=10, spacing=10)
    box.add_widget(Label(text=message))
    btn = Button(text="OK", size_hint_y=None, height=44)
    pop = Popup(title=title, content=box, size_hint=(0.8, 0.5))
    btn.bind(on_release=pop.dismiss)
    box.add_widget(btn)
    pop.open()

# =============== Screens ===============
class HomeScreen(Screen):
    """Add note (title, subject, content, picture) + Voice-to-Text"""
    def __init__(self, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.save_callback = save_callback
        self.selected_image_path = ""

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.title_input = TextInput(hint_text="Title / शीर्षक", multiline=False)
        self.subject_input = TextInput(hint_text="Subject / विषय", multiline=False)
        self.content_input = TextInput(
            hint_text="Write your note here... / अपना नोट लिखें",
            multiline=True, size_hint_y=0.5
        )

        row1 = BoxLayout(size_hint_y=None, height=48, spacing=8)
        pick_img_btn = Button(text="🖼️ Attach Picture")
        voice_btn = Button(text="🎤 Voice to Text")
        row1.add_widget(pick_img_btn); row1.add_widget(voice_btn)
        pick_img_btn.bind(on_release=self.open_file_picker)
        voice_btn.bind(on_release=self.voice_to_text)

        row2 = BoxLayout(size_hint_y=None, height=48, spacing=8)
        save_btn = Button(text="💾 Save Note")
        view_btn = Button(text="📚 View Notes")
        pics_btn = Button(text="🖼️ Student Pictures")
        quotes_btn = Button(text="💡 Daily Quote")
        for b in (save_btn, view_btn, pics_btn, quotes_btn):
            row2.add_widget(b)
        save_btn.bind(on_release=self._save)
        view_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "view"))
        pics_btn.bind(on_release=lambda *_: setattr(self.manager, "pictures", None) or setattr(self.manager, "current", "pictures"))
        quotes_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "quotes"))

        self.preview_img = Image(source="", size_hint_y=None, height=180, allow_stretch=True, keep_ratio=True)

        layout.add_widget(self.title_input)
        layout.add_widget(self.subject_input)
        layout.add_widget(self.content_input)
        layout.add_widget(self.preview_img)
        layout.add_widget(row1)
        layout.add_widget(row2)
        self.add_widget(layout)

    def open_file_picker(self, *_):
        chooser = FileChooserIconView(filters=["*.png","*.jpg","*.jpeg","*.webp","*.bmp"], path=os.getcwd())
        popup = Popup(title="Choose an image", content=chooser, size_hint=(0.9, 0.9))
        def _on_select(_inst, selection):
            if selection:
                self.selected_image_path = selection[0]
                self.preview_img.source = self.selected_image_path
                self.preview_img.reload()
                popup.dismiss()
        chooser.bind(on_submit=lambda inst, sel, touch: _on_select(inst, sel))
        popup.open()

    def voice_to_text(self, *_):
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                self.content_input.hint_text = "Listening... बोलिए..."
                audio = r.listen(source, timeout=6, phrase_time_limit=15)
            try:
                text = r.recognize_google(audio, language="hi-IN")
            except sr.UnknownValueError:
                text = r.recognize_google(audio, language="en-IN")
            prefix = "" if self.content_input.text.endswith((" ", "\n", "")) else " "
            self.content_input.text += prefix + text
        except Exception as e:
            self.content_input.text += f"\n[Voice failed: {e}]"
        finally:
            self.content_input.hint_text = "Write your note here... / अपना नोट लिखें"

    def _save(self, *_):
        title = self.title_input.text.strip() or "Untitled"
        subject = self.subject_input.text.strip() or "General"
        content = self.content_input.text.strip()
        if not (title or content):
            return
        note = {
            "title": title,
            "subject": subject,
            "content": content,
            "image": self.selected_image_path,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "pinned": False
        }
        self.save_callback(note)
        self.title_input.text = ""
        self.subject_input.text = ""
        self.content_input.text = ""
        self.selected_image_path = ""
        self.preview_img.source = ""

class ViewNotesScreen(Screen):
    """List with Search + Sort + Export PDF + Backup/Restore"""
    def __init__(self, open_callback, export_pdf_cb, backup_cb, restore_cb, **kwargs):
        super().__init__(**kwargs)
        self.open_callback = open_callback
        self.export_pdf_cb = export_pdf_cb
        self.backup_cb = backup_cb
        self.restore_cb = restore_cb
        self.search_query = ""
        self.sort_mode = "Pinned, Date ↓"

    def on_pre_enter(self, *_):
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=10, spacing=8)

        # Top controls: Search + Sort + Export/Backup/Restore
        controls = BoxLayout(size_hint_y=None, height=48, spacing=8)
        self.search_input = TextInput(hint_text="🔍 Search title/subject/content", multiline=False)
        self.search_input.bind(text=lambda _w, t: self._on_search(t))
        sort_btn = Button(text=f"Sort: {self.sort_mode}")
        sort_btn.bind(on_release=self._cycle_sort)

        export_btn = Button(text="🧾 Export PDF")
        backup_btn = Button(text="☁️ Backup")
        restore_btn = Button(text="📥 Restore")

        export_btn.bind(on_release=lambda *_: self.export_pdf_cb())
        backup_btn.bind(on_release=lambda *_: self.backup_cb())
        restore_btn.bind(on_release=lambda *_: self.restore_cb())

        for w in (self.search_input, sort_btn, export_btn, backup_btn, restore_btn):
            controls.add_widget(w)
        root.add_widget(controls)

        # Notes list
        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=8)
        box.bind(minimum_height=box.setter("height"))

        notes = self._get_filtered_sorted()

        if not notes:
            box.add_widget(Label(text="No matching notes.", size_hint_y=None, height=40))

        for idx, n in enumerate(notes):
            title = n.get("title", "Untitled")
            subject = n.get("subject", "General")
            date = n.get("date", "")
            content = n.get("content", "")
            snippet = (content[:90] + "…") if len(content) > 90 else content
            has_img = "🖼️" if n.get("image") else " "
            pin = "📌 " if n.get("pinned") else ""
            btn = Button(
                text=f"{pin}{has_img} {title}  ({subject})\n🕒 {date}\n{snippet}",
                size_hint_y=None, height=92, halign="left", valign="middle", text_size=(900, None)
            )
            # Map idx to real index via helper:
            real_index = App.get_running_app().notes.index(n)
            btn.bind(on_release=lambda _b, i=real_index: self.open_callback(i))
            box.add_widget(btn)

        scroll.add_widget(box)
        root.add_widget(scroll)

        back = Button(text="⬅ Back", size_hint_y=None, height=48)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back)

        self.add_widget(root)

    def _on_search(self, text):
        self.search_query = (text or "").strip().lower()
        self._build()

    def _cycle_sort(self, *_):
        modes = ["Pinned, Date ↓", "Date ↓", "Date ↑", "Title A–Z", "Title Z–A", "Subject A–Z", "Subject Z–A"]
        i = modes.index(self.sort_mode) if self.sort_mode in modes else 0
        self.sort_mode = modes[(i + 1) % len(modes)]
        self._build()

    def _get_filtered_sorted(self):
        notes = App.get_running_app().notes[:]
        # filter
        if self.search_query:
            q = self.search_query
            def m(n):
                return q in n.get("title","").lower() or q in n.get("subject","").lower() or q in n.get("content","").lower()
            notes = [n for n in notes if m(n)]
        # sort
        if self.sort_mode == "Pinned, Date ↓":
            notes.sort(key=lambda n: (not n.get("pinned", False), n.get("date","")), reverse=True)
        elif self.sort_mode == "Date ↓":
            notes.sort(key=lambda n: n.get("date",""), reverse=True)
        elif self.sort_mode == "Date ↑":
            notes.sort(key=lambda n: n.get("date",""))
        elif self.sort_mode == "Title A–Z":
            notes.sort(key=lambda n: n.get("title","").lower())
        elif self.sort_mode == "Title Z–A":
            notes.sort(key=lambda n: n.get("title","").lower(), reverse=True)
        elif self.sort_mode == "Subject A–Z":
            notes.sort(key=lambda n: n.get("subject","").lower())
        elif self.sort_mode == "Subject Z–A":
            notes.sort(key=lambda n: n.get("subject","").lower(), reverse=True)
        return notes

class NoteDetailScreen(Screen):
    """Single note view with image + TTS + Edit/Delete/Pin"""
    def __init__(self, edit_callback, delete_callback, pin_callback, **kwargs):
        super().__init__(**kwargs)
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback
        self.pin_callback = pin_callback
        self.current_real_index = None
        self.tts = pyttsx3.init()
        try:
            rate = self.tts.getProperty('rate')
            self.tts.setProperty('rate', int(rate * 0.9))
        except Exception:
            pass

    def speak(self, text):
        try:
            for v in self.tts.getProperty('voices'):
                name = (v.name or "").lower()
                lang = ",".join(getattr(v, "languages", [])).lower() if hasattr(v, "languages") else ""
                if "hindi" in name or "hi_" in lang or "hi-" in lang:
                    self.tts.setProperty('voice', v.id)
                    break
        except Exception:
            pass
        self.tts.say(text)
        self.tts.runAndWait()

    def show_note(self, real_index):
        self.current_real_index = real_index
        self.clear_widgets()
        app = App.get_running_app()
        n = app.notes[real_index]

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(Label(text=f"📖 {n['title']}", font_size=22))
        layout.add_widget(Label(text=f"📘 Subject: {n['subject']}", font_size=16))
        layout.add_widget(Label(text=f"🕒 {n['date']}", font_size=14))

        if n.get("image") and os.path.exists(n["image"]):
            layout.add_widget(Image(source=n["image"], size_hint_y=None, height=260, allow_stretch=True, keep_ratio=True))

        content_lbl = Label(text=n.get("content", ""), halign="left", valign="top")
        content_lbl.bind(size=lambda *_: setattr(content_lbl, "text_size", (content_lbl.width, None)))
        layout.add_widget(content_lbl)

        row = BoxLayout(size_hint_y=None, height=48, spacing=8)
        speak_btn = Button(text="🔊 Speak Note")
        edit_btn = Button(text="✏ Edit")
        pin_btn = Button(text="📌 Pin/Unpin")
        del_btn = Button(text="🗑 Delete")

        speak_btn.bind(on_release=lambda *_: self.speak(f"{n['title']} - {n['subject']} - {n.get('content','')}"))
        edit_btn.bind(on_release=lambda *_: self.edit_callback(self.current_real_index))
        pin_btn.bind(on_release=lambda *_: self.pin_callback(self.current_real_index))
        del_btn.bind(on_release=lambda *_: self.delete_callback(self.current_real_index))

        for b in (speak_btn, edit_btn, pin_btn, del_btn):
            row.add_widget(b)
        layout.add_widget(row)

        back = Button(text="⬅ Back", size_hint_y=None, height=48)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "view"))
        layout.add_widget(back)
        self.add_widget(layout)

class PicturesScreen(Screen):
    """Auto gallery from project root and /pictures"""
    def on_pre_enter(self, *_):
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=10, spacing=10)
        root.add_widget(Label(text="🖼️ Student Pictures Gallery", font_size=20))

        imgs = list_all_images()
        if not imgs:
            root.add_widget(Label(text="No images found.\nPut pictures in this folder or 'pictures/' folder.",
                                  size_hint_y=None, height=80))
        else:
            scroll = ScrollView()
            grid = GridLayout(cols=2, spacing=8, size_hint_y=None, padding=2)
            grid.bind(minimum_height=grid.setter("height"))
            for path in imgs:
                thumb = Image(source=path, size_hint_y=None, height=200, allow_stretch=True, keep_ratio=True)
                def open_full(_i, p=path):
                    img = Image(source=p, allow_stretch=True, keep_ratio=True)
                    wrap = BoxLayout(orientation="vertical", padding=8, spacing=6)
                    wrap.add_widget(img)
                    wrap.add_widget(Label(text=os.path.basename(p)))
                    close = Button(text="Close", size_hint_y=None, height=44)
                    pop = Popup(title="Preview", content=wrap, size_hint=(0.9, 0.9))
                    close.bind(on_release=pop.dismiss)
                    wrap.add_widget(close)
                    pop.open()
                thumb.bind(on_touch_down=lambda w, t, _thumb=thumb: (open_full(_thumb) if _thumb.collide_point(*t.pos) and t.is_double_tap else None))
                grid.add_widget(thumb)
            scroll.add_widget(grid)
            root.add_widget(scroll)

        back = Button(text="⬅ Back", size_hint_y=None, height=48)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back)
        self.add_widget(root)

class QuotesScreen(Screen):
    """Daily quote (English + Hindi)"""
    def on_pre_enter(self, *_):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        idx = int(datetime.now().strftime("%Y%m%d")) % len(QUOTES)
        en, hi = QUOTES[idx]

        layout.add_widget(Label(text="💡 Today's Quote", font_size=20))
        layout.add_widget(Label(text=en, font_size=18, halign="center"))
        try:
            layout.add_widget(Label(text=hi, font_size=18, halign="center", font_name="HindiFont"))
        except Exception:
            layout.add_widget(Label(text=hi, font_size=18, halign="center"))

        back = Button(text="⬅ Back", size_hint_y=None, height=48)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "home"))
        layout.add_widget(back)
        self.add_widget(layout)

# =============== App Controller ===============
class NotesApp(App):
    def build(self):
        self.notes = load_notes()
        self.sm = ScreenManager()

        self.home = HomeScreen(self.add_note, name="home")
        self.sm.add_widget(self.home)

        self.view = ViewNotesScreen(self.open_note, self.export_pdf, self.backup_notes, self.restore_notes, name="view")
        self.sm.add_widget(self.view)

        self.detail = NoteDetailScreen(self.edit_note, self.delete_note, self.pin_note, name="detail")
        self.sm.add_widget(self.detail)

        self.pictures = PicturesScreen(name="pictures")
        self.sm.add_widget(self.pictures)

        self.quotes = QuotesScreen(name="quotes")
        self.sm.add_widget(self.quotes)
        return self.sm

    # -------- CRUD --------
    def add_note(self, note):
        self.notes.append(note)
        save_notes(self.notes)
        self.sm.current = "view"

    def open_note(self, real_index):
        self.detail.show_note(real_index)
        self.sm.current = "detail"

    def edit_note(self, real_index):
        n = self.notes[real_index]
        self.home.title_input.text = n["title"]
        self.home.subject_input.text = n["subject"]
        self.home.content_input.text = n["content"]
        self.home.selected_image_path = n.get("image", "")
        self.home.preview_img.source = n.get("image", "")
        del self.notes[real_index]
        save_notes(self.notes)
        self.sm.current = "home"

    def delete_note(self, real_index):
        if 0 <= real_index < len(self.notes):
            del self.notes[real_index]
            save_notes(self.notes)
        self.sm.current = "view"

    def pin_note(self, real_index):
        self.notes[real_index]["pinned"] = not self.notes[real_index].get("pinned", False)
        save_notes(self.notes)
        self.detail.show_note(real_index)

    # -------- Export PDF --------
    def export_pdf(self):
        if not REPORTLAB_AVAILABLE:
            show_info("Install needed", "PDF export needs reportlab.\nRun:\n\npip install reportlab")
            return
        out = "notes_export.pdf"
        c = canvas.Canvas(out, pagesize=A4)
        W, H = A4
        left, top = 2*cm, H - 2*cm
        y = top

        def write_line(text, size=11, gap=14, bold=False):
            nonlocal y
            if y < 2*cm:
                c.showPage(); y = top
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            c.drawString(left, y, text)
            y -= gap

        for n in sorted(self.notes, key=lambda k: (not k.get("pinned", False), k.get("date","")), reverse=True):
            write_line(f"📖 {n.get('title','Untitled')}  ({n.get('subject','General')})", size=12, gap=16, bold=True)
            write_line(f"🕒 {n.get('date','')}", size=10, gap=14)
            # content wrap simple:
            content = n.get("content","").splitlines() or [""]
            for line in content:
                for chunk in [line[i:i+90] for i in range(0, len(line), 90)]:
                    write_line(chunk, size=11, gap=13)
            # image (optional)
            img = n.get("image")
            if img and os.path.exists(img):
                try:
                    y -= 6
                    if y < 8*cm:
                        c.showPage(); y = top
                    iw, ih = ImageReader(img).getSize()
                    maxw, maxh = W - 4*cm, 8*cm
                    scale = min(maxw/iw, maxh/ih)
                    dw, dh = iw*scale, ih*scale
                    c.drawImage(ImageReader(img), left, y - dh, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                    y -= (dh + 12)
                except Exception:
                    write_line("[image failed]", size=10)
            y -= 10

        c.save()
        show_info("Exported", f"Saved: {out}")

    # -------- Backup / Restore (choose location) --------
    def backup_notes(self):
        # save a copy to chosen folder as notes_backup.json
        chooser = FileChooserIconView(path=os.getcwd(), dirselect=True)
        pop = Popup(title="Choose folder to save backup", content=chooser, size_hint=(0.9, 0.9))
        def _save(_inst, sel, *_a):
            folder = sel[0] if sel else ""
            if folder and os.path.isdir(folder):
                out = os.path.join(folder, "notes_backup.json")
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(self.notes, f, ensure_ascii=False, indent=2)
                pop.dismiss()
                show_info("Backup saved", f"Saved to:\n{out}\n\nTip: choose a cloud-synced folder (OneDrive/Drive).")
        chooser.bind(on_submit=_save)
        pop.open()

    def restore_notes(self):
        # choose a JSON file to load
        chooser = FileChooserIconView(path=os.getcwd(), filters=["*.json"])
        pop = Popup(title="Choose backup JSON to restore", content=chooser, size_hint=(0.9, 0.9))
        def _load(_inst, sel, *_a):
            if sel:
                path = sel[0]
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        self.notes = data
                        save_notes(self.notes)
                        pop.dismiss()
                        show_info("Restored", "Backup restored successfully.")
                        # refresh view if open
                        if self.sm.current == "view":
                            self.view._build()
                    else:
                        show_info("Invalid file", "Selected JSON is not a notes list.")
                except Exception as e:
                    show_info("Error", f"Failed to restore:\n{e}")
        chooser.bind(on_submit=_load)
        pop.open()

if __name__ == "__main__":
    NotesApp().run()
