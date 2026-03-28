"""
Face Health Analyzer — Premium Edition
Real-time facial health screening with friendly insights,
personalized recommendations, and exportable health reports.
"""

import cv2, os, time, math, webbrowser, threading
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from collections import deque
from datetime import datetime

# ─────────────── Design Tokens ───────────────
BG          = "#0d1117"
BG_CARD     = "#161b22"
BG_ELEVATED = "#1c2333"
BG_HOVER    = "#21283b"
ACCENT      = "#58a6ff"
ACCENT2     = "#79c0ff"
GREEN       = "#3fb950"
GREEN_DIM   = "#1a4028"
YELLOW      = "#d29922"
YELLOW_DIM  = "#3d2e00"
RED         = "#f85149"
RED_DIM     = "#4a1c1c"
ORANGE      = "#db6d28"
PURPLE      = "#bc8cff"
CYAN        = "#39d353"
TXT         = "#e6edf3"
TXT2        = "#8b949e"
TXT3        = "#484f58"
BORDER      = "#30363d"
RADIUS      = 12

# ─────────────── Friendly Tips Database ───────────────
TIPS = {
    "fever": [
        "💧  Stay hydrated — drink water, herbal teas, or clear broths.",
        "🛌  Rest well and avoid strenuous activities.",
        "🌡️  Monitor your temperature regularly.",
        "👨‍⚕️  See a doctor if fever persists over 48 hours.",
    ],
    "pallor": [
        "🥬  Eat iron-rich foods: spinach, lentils, red meat.",
        "🍊  Pair iron foods with Vitamin C for better absorption.",
        "😴  Ensure 7–9 hours of quality sleep each night.",
        "🩸  Consider getting a blood test for anemia.",
    ],
    "eye_irritation": [
        "👁️  Follow the 20-20-20 rule: every 20 min look 20 ft away for 20 sec.",
        "💧  Use preservative-free artificial tears.",
        "🚫  Avoid rubbing your eyes — it worsens irritation.",
        "😎  Wear sunglasses outdoors to reduce strain.",
    ],
    "fatigue": [
        "☀️  Get 15 min of morning sunlight to regulate your circadian rhythm.",
        "🏃  Light exercise (a 20-min walk) boosts energy levels.",
        "📵  Avoid screens 1 hour before bedtime.",
        "🥗  Eat balanced meals and avoid excess sugar.",
    ],
    "dry_skin": [
        "💦  Drink at least 8 glasses of water daily.",
        "🧴  Apply moisturizer right after washing your face.",
        "🚿  Avoid hot showers — use lukewarm water instead.",
        "🏠  Use a humidifier in dry weather.",
    ],
    "stress": [
        "🧘  Practice deep breathing: inhale 4s, hold 4s, exhale 6s.",
        "🚶  Take a 10-minute walk to clear your mind.",
        "💤  Prioritize 7–9 hours of sleep tonight.",
        "📵  Step away from screens for at least 15 minutes.",
        "🎵  Listen to calming music or nature sounds.",
    ],
    "healthy": [
        "🎉  Great job! Keep maintaining your healthy lifestyle.",
        "🥦  Continue eating a balanced, nutrient-rich diet.",
        "🏋️  Stay active with at least 30 min of exercise daily.",
        "😊  Your well-being matters — keep smiling!",
    ],
}


class FaceAnalyzer:
    """Computer-vision based facial health screening."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml")
        self.eye_open_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")
        # Blink / closure tracking
        self.blink_history = deque(maxlen=150)   # ~5 sec at 30fps
        self.ear_history = deque(maxlen=30)

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))
        return faces, gray

    # ── Individual analyses ─────────────────────────────
    def _skin(self, roi_bgr):
        h, w = roi_bgr.shape[:2]
        forehead = roi_bgr[int(h*0.05):int(h*0.25), int(w*0.25):int(w*0.75)]
        cheek_l  = roi_bgr[int(h*0.45):int(h*0.7),  int(w*0.05):int(w*0.35)]
        cheek_r  = roi_bgr[int(h*0.45):int(h*0.7),  int(w*0.65):int(w*0.95)]

        avg_r = np.mean(roi_bgr[:,:,2])
        avg_g = np.mean(roi_bgr[:,:,1])
        redness = avg_r / (avg_g + 1)

        lab = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2LAB)
        uniformity = round(100 - min(np.std(lab[:,:,0]), 40) * 2.5, 1)

        hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        yellowish = bool(15 < np.mean(hsv[:,:,0]) < 35 and np.mean(hsv[:,:,1]) > 80)

        sym = 50.0
        if cheek_l.size and cheek_r.size:
            diff = np.linalg.norm(np.mean(cheek_l, axis=(0,1)) - np.mean(cheek_r, axis=(0,1)))
            sym = round(max(0, 100 - diff * 2), 1)

        if redness > 1.45:
            status, concern, score = "Flushed / Red", "Elevated redness — possible fever or inflammation", max(20, 100-int((redness-1.45)*200))
            tag = "fever"
        elif redness < 0.95:
            status, concern, score = "Pale", "Reduced colour — possible fatigue or low iron", max(30, 100-int((0.95-redness)*200))
            tag = "pallor"
        else:
            status, concern, score = "Healthy", "Skin colour looks normal and well-balanced", min(100, int(70+(1.2-abs(redness-1.2))*50))
            tag = "healthy"

        return dict(status=status, concern=concern, score=score, redness=round(redness,2),
                    uniformity=uniformity, yellowish=yellowish, symmetry=sym, tag=tag)

    def _eyes(self, gray_roi, bgr_roi):
        eyes = self.eye_cascade.detectMultiScale(gray_roi, 1.1, 5, minSize=(20,20))
        n = len(eyes)
        if n < 2:
            return dict(status="Not fully visible", concern="Ensure both eyes are visible for best results",
                        score=55, redness=0, dark_circles="Unknown", detected=n, tag="healthy")

        reds = []
        for (ex,ey,ew,eh) in eyes[:2]:
            e = bgr_roi[ey:ey+eh, ex:ex+ew]
            if e.size: reds.append(np.mean(e[:,:,2])/(np.mean(e[:,:,1])+np.mean(e[:,:,0])+1)*2)
        avg_red = np.mean(reds) if reds else 0

        dark = "Minimal"
        for (ex,ey,ew,eh) in eyes[:2]:
            under = bgr_roi[ey+eh:ey+eh+int(eh*0.4), ex:ex+ew]
            if under.size and np.mean(under) < np.mean(bgr_roi)*0.75:
                dark = "Visible"; break

        if avg_red > 0.85:
            status,concern,score,tag = "Irritated","Eyes appear red — possible allergy or strain",max(20,100-int((avg_red-0.85)*300)),"eye_irritation"
        elif avg_red > 0.7:
            status,concern,score,tag = "Mildly strained","Slight redness — could be screen fatigue",65,"fatigue"
        else:
            status,concern,score,tag = "Clear & bright","Eyes look healthy with no visible irritation",min(95,int(70+(0.7-avg_red)*100)),"healthy"

        return dict(status=status,concern=concern,score=score,redness=round(avg_red,2),
                    dark_circles=dark,detected=n,tag=tag)

    def _eye_closure(self, gray_roi, bgr_roi):
        """Estimate eye closure % using Eye Aspect Ratio from contours."""
        h, w = gray_roi.shape[:2]
        # Focus on eye region (upper 20-55% of face)
        eye_strip = gray_roi[int(h*0.18):int(h*0.55), :]
        eye_strip_bgr = bgr_roi[int(h*0.18):int(h*0.55), :]

        # Detect eyes using multiple cascades for robust detection
        eyes_open = self.eye_cascade.detectMultiScale(eye_strip, 1.05, 6, minSize=(20,15))
        eyes_alt = self.eye_open_cascade.detectMultiScale(eye_strip, 1.05, 6, minSize=(20,15))

        # EAR estimation via contour bounding boxes
        ear_values = []
        for eyes_list in [eyes_open, eyes_alt]:
            for (ex, ey, ew, eh) in eyes_list[:2]:
                # Eye Aspect Ratio approximation: height / width
                ear = eh / ew if ew > 0 else 0
                ear_values.append(ear)

        if ear_values:
            avg_ear = np.mean(ear_values)
            self.ear_history.append(avg_ear)
        else:
            avg_ear = 0.0
            self.ear_history.append(0.15)  # Assume mostly closed if no eyes found

        # Calculate closure percentage
        # Typical open EAR ~ 0.35-0.55, closed ~ 0.1-0.2
        if avg_ear >= 0.45:
            closure_pct = 0
        elif avg_ear <= 0.15:
            closure_pct = 100
        else:
            closure_pct = round(max(0, min(100, (0.45 - avg_ear) / 0.30 * 100)))

        # Track blinks (rapid closure-open transitions)
        is_closed = closure_pct > 50
        self.blink_history.append(is_closed)

        # Count blinks: closed->open transitions in history
        blinks = 0
        for i in range(1, len(self.blink_history)):
            if self.blink_history[i-1] and not self.blink_history[i]:
                blinks += 1

        # Estimate blink rate per minute (history is ~5sec)
        history_secs = len(self.blink_history) / 30.0
        blink_rate = round(blinks / history_secs * 60) if history_secs > 0.5 else 0

        # Smoothed EAR from history
        smooth_ear = np.mean(self.ear_history) if self.ear_history else avg_ear

        # Eye openness (inverted closure)
        openness = 100 - closure_pct

        # Droopiness indicator
        if openness >= 70:
            droop_status = "Wide open"
        elif openness >= 45:
            droop_status = "Partially open"
        elif openness >= 20:
            droop_status = "Droopy / Heavy"
        else:
            droop_status = "Nearly closed"

        return dict(
            closure_pct=closure_pct, openness=openness,
            ear=round(avg_ear, 3), smooth_ear=round(smooth_ear, 3),
            blink_rate=blink_rate, droop_status=droop_status,
            eyes_found=len(eyes_open) + len(eyes_alt),
        )

    def _stress(self, eye_closure, eyes, skin):
        """Compute composite stress level from multiple indicators."""
        factors = []

        # Factor 1: Eye closure/droopiness (heavy eyes = fatigue/stress)
        closure = eye_closure["closure_pct"]
        if closure > 50:
            factors.append(("Heavy/droopy eyes", 85))
        elif closure > 30:
            factors.append(("Partially narrowed eyes", 55))
        else:
            factors.append(("Eyes alert and open", 15))

        # Factor 2: Eye strain (redness)
        eye_score = eyes.get("score", 70)
        if eye_score < 50:
            factors.append(("Eye strain detected", 80))
        elif eye_score < 70:
            factors.append(("Mild eye strain", 50))
        else:
            factors.append(("Eyes relaxed", 10))

        # Factor 3: Blink rate (normal ~15-20/min, stress: >25 or <10)
        br = eye_closure["blink_rate"]
        if br > 28:
            factors.append(("Rapid blinking", 75))
        elif br < 8 and br > 0:
            factors.append(("Infrequent blinking", 60))
        else:
            factors.append(("Normal blink rate", 10))

        # Factor 4: Dark circles
        if eyes.get("dark_circles") == "Visible":
            factors.append(("Dark circles present", 55))

        # Factor 5: Skin tension (flushed skin can correlate w/ stress)
        if skin.get("status") == "Flushed / Red":
            factors.append(("Skin flushing", 50))

        # Composite stress score (0 = calm, 100 = very stressed)
        stress_val = int(np.mean([f[1] for f in factors]))

        if stress_val >= 65:
            level, color, concern = "High", RED, "Multiple stress indicators detected — consider taking a break"
            tag = "stress"
        elif stress_val >= 40:
            level, color, concern = "Moderate", YELLOW, "Some signs of tension — try relaxation techniques"
            tag = "stress"
        elif stress_val >= 20:
            level, color, concern = "Low", ACCENT, "Minor indicators — you're doing okay"
            tag = "healthy"
        else:
            level, color, concern = "Relaxed", GREEN, "You appear calm and well-rested"
            tag = "healthy"

        return dict(
            stress_score=stress_val, level=level, color=color,
            concern=concern, factors=factors, tag=tag,
        )

    def _texture(self, gray_roi):
        var = cv2.Laplacian(gray_roi, cv2.CV_64F).var()
        if var > 800:
            s,c,sc,tag = "Rough / Dry","Skin texture is coarser than normal",max(30,100-int((var-800)/20)),"dry_skin"
        elif var < 100:
            s,c,sc,tag = "Smooth","Skin texture looks very smooth",92,"healthy"
        else:
            s,c,sc,tag = "Normal","Skin texture is within a healthy range",min(95,int(60+(800-var)/20)),"healthy"
        return dict(status=s,concern=c,score=sc,variance=round(var,1),tag=tag)

    def _shape(self, rect):
        x,y,w,h = rect
        ar = round(h/w if w else 1, 2)
        if ar < 1.0:
            note,swell = "Wider than typical","Possible"
        elif ar > 1.6:
            note,swell = "More elongated shape","Unlikely"
        else:
            note,swell = "Well-proportioned","None detected"
        return dict(note=note,swelling=swell,ratio=ar,w=w,h=h)

    # ── Full pipeline ──────────────────────────────────
    def analyze(self, frame):
        faces, gray = self.detect_faces(frame)
        if len(faces) == 0:
            return None
        x,y,w,h = max(faces, key=lambda f: f[2]*f[3])
        bgr = frame[y:y+h, x:x+w]
        gr  = gray[y:y+h, x:x+w]
        if bgr.size == 0:
            return None

        skin = self._skin(bgr)
        eyes = self._eyes(gr, bgr)
        eye_closure = self._eye_closure(gr, bgr)
        tex  = self._texture(gr)
        shape = self._shape((x,y,w,h))
        stress = self._stress(eye_closure, eyes, skin)

        # Stress penalizes overall score slightly
        stress_penalty = max(0, (stress["stress_score"] - 30) * 0.15)
        overall = max(0, min(100, int(np.mean([skin["score"], eyes["score"], tex["score"]]) - stress_penalty)))

        # Collect unique tags for tips
        tags = set()
        for d in [skin, eyes, tex]:
            tags.add(d["tag"])
        if stress["tag"] != "healthy":
            tags.add(stress["tag"])
        tags.discard("healthy")
        if not tags:
            tags.add("healthy")

        # Build friendly conditions list
        conds = []
        if skin["status"] == "Flushed / Red":
            conds.append(("Elevated Skin Redness", "May indicate fever or irritation", RED))
        if skin["status"] == "Pale":
            conds.append(("Skin Pallor", "Could indicate fatigue or low iron", ORANGE))
        if skin["yellowish"]:
            conds.append(("Yellowish Tint", "Unusual skin tone detected", YELLOW))
        if eyes["status"] == "Irritated":
            conds.append(("Eye Redness", "Possible allergy or digital strain", RED))
        if eyes["dark_circles"] == "Visible":
            conds.append(("Dark Under-Eye Circles", "Sign of insufficient rest", ORANGE))
        if tex["status"] == "Rough / Dry":
            conds.append(("Skin Dryness", "Skin texture rougher than normal", YELLOW))
        if shape["swelling"] == "Possible":
            conds.append(("Facial Puffiness", "Face appears wider than expected", YELLOW))
        if eye_closure["closure_pct"] > 40:
            conds.append(("Droopy / Heavy Eyes", f"Eyes {eye_closure['closure_pct']}% closed — possible fatigue", ORANGE))
        if stress["stress_score"] >= 50:
            conds.append((f"Stress Level: {stress['level']}", stress["concern"], stress["color"]))
        if not conds:
            conds.append(("All Clear!", "No health concerns detected", GREEN))

        # Gather tips
        all_tips = []
        for t in tags:
            all_tips.extend(TIPS.get(t, []))

        if overall >= 75:
            verdict, vcolor, emoji = "Looking Healthy!", GREEN, "😊"
        elif overall >= 50:
            verdict, vcolor, emoji = "Minor Concerns", YELLOW, "🤔"
        else:
            verdict, vcolor, emoji = "Needs Attention", RED, "😟"

        return dict(
            face=(x,y,w,h), skin=skin, eyes=eyes, eye_closure=eye_closure,
            stress=stress, texture=tex, shape=shape,
            overall=overall, conditions=conds, tips=all_tips, tags=list(tags),
            verdict=verdict, verdict_color=vcolor, emoji=emoji,
            time=datetime.now().strftime("%I:%M:%S %p"),
            date=datetime.now().strftime("%B %d, %Y"),
        )


# ─────────────── Rounded-rect helper ───────────────
def _rr(canvas, x1, y1, x2, y2, r=10, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2,
           x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1, x1+r,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class ProgressBar(tk.Canvas):
    """Animated circular-feel horizontal progress bar."""

    def __init__(self, parent, width=200, height=10, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=BG_CARD, highlightthickness=0, **kw)
        self.w = width
        self.h = height
        self._val = 0

    def set(self, val, color=GREEN):
        self.delete("all")
        # Track
        _rr(self, 0, 0, self.w, self.h, r=5, fill=BG, outline="")
        # Fill
        fw = max(8, int(self.w * val / 100))
        _rr(self, 0, 0, fw, self.h, r=5, fill=color, outline="")


# ─────────────── Main Application ───────────────
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Health Analyzer")
        self.root.geometry("1360x800")
        self.root.configure(bg=BG)
        self.root.minsize(1100, 700)

        self.analyzer = FaceAnalyzer()
        self.cap = None
        self.running = False
        self.result = None
        self.history = []
        self.current_frame = None
        self.fps_q = deque(maxlen=30)
        self.last_t = time.time()
        self._photo = None

        self._style()
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    # ── ttk styling ────────────────────────────────────
    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Dark.TFrame", background=BG)
        s.configure("Card.TFrame", background=BG_CARD)
        s.configure("TScrollbar", background=BG_CARD, troughcolor=BG,
                     arrowcolor=TXT3, borderwidth=0)

    # ── Build UI ───────────────────────────────────────
    def _build(self):
        # ─ Header ─
        hdr = tk.Frame(self.root, bg=BG_ELEVATED, height=56)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        lf = tk.Frame(hdr, bg=BG_ELEVATED)
        lf.pack(side=tk.LEFT, padx=20)
        tk.Label(lf, text="🩺", font=("Segoe UI Emoji", 20),
                 bg=BG_ELEVATED, fg=ACCENT).pack(side=tk.LEFT, padx=(0,6))
        tk.Label(lf, text="Face Health Analyzer", font=("Segoe UI", 16, "bold"),
                 bg=BG_ELEVATED, fg=TXT).pack(side=tk.LEFT)
        tk.Label(lf, text="  AI-Powered Facial Screening",
                 font=("Segoe UI", 9), bg=BG_ELEVATED, fg=TXT3).pack(side=tk.LEFT, padx=(8,0))

        rf = tk.Frame(hdr, bg=BG_ELEVATED)
        rf.pack(side=tk.RIGHT, padx=20)
        self.status_dot = tk.Label(rf, text="●", font=("Segoe UI", 12),
                                    bg=BG_ELEVATED, fg=RED)
        self.status_dot.pack(side=tk.LEFT, padx=(0,4))
        self.status_lbl = tk.Label(rf, text="Camera Off", font=("Segoe UI", 10),
                                    bg=BG_ELEVATED, fg=TXT2)
        self.status_lbl.pack(side=tk.LEFT)

        # ─ Body ─
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Left column
        left = tk.Frame(body, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,6))

        # Camera card
        cam_card = tk.Frame(left, bg=BG_CARD, highlightbackground=BORDER,
                             highlightthickness=1)
        cam_card.pack(fill=tk.BOTH, expand=True)

        cam_hdr = tk.Frame(cam_card, bg=BG_CARD)
        cam_hdr.pack(fill=tk.X, padx=14, pady=(10,4))
        tk.Label(cam_hdr, text="📹  Live Camera", font=("Segoe UI", 11, "bold"),
                 bg=BG_CARD, fg=TXT).pack(side=tk.LEFT)
        self.fps_lbl = tk.Label(cam_hdr, text="", font=("Segoe UI", 9),
                                 bg=BG_CARD, fg=TXT3)
        self.fps_lbl.pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(cam_card, bg="#000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        # Instruction overlay text (shown when camera is off)
        self.canvas.update_idletasks()
        self.welcome_id = None
        self._show_welcome()

        # Controls
        ctrl = tk.Frame(left, bg=BG, height=52)
        ctrl.pack(fill=tk.X, pady=(8,0))
        ctrl.pack_propagate(False)

        bs = dict(font=("Segoe UI", 11, "bold"), relief=tk.FLAT, cursor="hand2",
                  padx=20, pady=7, bd=0, activeforeground="white")

        self.btn_cam = tk.Button(ctrl, text="▶  Start Camera", bg=ACCENT, fg="white",
                                  activebackground="#4090e0", command=self._toggle_cam, **bs)
        self.btn_cam.pack(side=tk.LEFT, padx=(0,8))

        self.btn_scan = tk.Button(ctrl, text="🔍  Scan My Face", bg="#238636", fg="white",
                                   activebackground="#2ea043", command=self._analyze,
                                   state=tk.DISABLED, **bs)
        self.btn_scan.pack(side=tk.LEFT, padx=(0,8))

        self.btn_report = tk.Button(ctrl, text="📄  Export Report", bg=BG_ELEVATED, fg=TXT2,
                                     activebackground=BG_HOVER, command=self._export,
                                     state=tk.DISABLED, **bs)
        self.btn_report.pack(side=tk.LEFT, padx=(0,8))

        self.auto_var = tk.BooleanVar()
        tk.Checkbutton(ctrl, text="Auto-scan", variable=self.auto_var,
                       bg=BG, fg=TXT2, selectcolor=BG_CARD, activebackground=BG,
                       activeforeground=TXT, font=("Segoe UI", 10),
                       command=self._toggle_auto).pack(side=tk.LEFT, padx=8)

        # Right column — results
        self.right = tk.Frame(body, bg=BG, width=400)
        self.right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6,0))
        self.right.pack_propagate(False)

        self._build_results()

    def _show_welcome(self):
        self.canvas.delete("welcome")
        self.canvas.update_idletasks()
        cw, ch = max(self.canvas.winfo_width(),400), max(self.canvas.winfo_height(),300)
        self.canvas.create_text(cw//2, ch//2 - 30, text="📷",
                                font=("Segoe UI Emoji",40), fill=TXT3, tags="welcome")
        self.canvas.create_text(cw//2, ch//2 + 30,
                                text="Click 'Start Camera' to begin",
                                font=("Segoe UI",13), fill=TXT3, tags="welcome")
        self.canvas.create_text(cw//2, ch//2 + 55,
                                text="Position your face clearly in front of the camera",
                                font=("Segoe UI",10), fill=TXT3, tags="welcome")

    # ── Results panel ──────────────────────────────────
    def _build_results(self):
        # Verdict banner
        self.vcard = tk.Frame(self.right, bg=BG_CARD, highlightbackground=BORDER,
                               highlightthickness=1)
        self.vcard.pack(fill=tk.X, pady=(0,6))

        tk.Label(self.vcard, text="YOUR HEALTH SNAPSHOT", font=("Segoe UI", 8, "bold"),
                 bg=BG_CARD, fg=TXT3, anchor=tk.W).pack(padx=16, pady=(14,0), anchor=tk.W)

        ef = tk.Frame(self.vcard, bg=BG_CARD)
        ef.pack(fill=tk.X, padx=16)
        self.emoji_lbl = tk.Label(ef, text="🔬", font=("Segoe UI Emoji",32),
                                   bg=BG_CARD, fg=TXT3)
        self.emoji_lbl.pack(side=tk.LEFT, padx=(0,10))

        vf = tk.Frame(ef, bg=BG_CARD)
        vf.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.verdict_lbl = tk.Label(vf, text="Waiting for scan...",
                                     font=("Segoe UI",18,"bold"), bg=BG_CARD, fg=TXT3,
                                     anchor=tk.W)
        self.verdict_lbl.pack(anchor=tk.W)
        self.score_lbl = tk.Label(vf, text="", font=("Segoe UI",11),
                                   bg=BG_CARD, fg=TXT2, anchor=tk.W)
        self.score_lbl.pack(anchor=tk.W)

        self.score_bar = ProgressBar(self.vcard, width=368, height=8)
        self.score_bar.pack(padx=16, pady=(4,14))

        # Scrollable detail area
        outer = tk.Frame(self.right, bg=BG)
        outer.pack(fill=tk.BOTH, expand=True)

        self.res_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=self.res_canvas.yview)
        self.res_inner = tk.Frame(self.res_canvas, bg=BG)
        self.res_inner.bind("<Configure>",
                             lambda e: self.res_canvas.configure(scrollregion=self.res_canvas.bbox("all")))
        self.res_canvas.create_window((0,0), window=self.res_inner, anchor=tk.NW, width=388)
        self.res_canvas.configure(yscrollcommand=sb.set)
        self.res_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse-wheel scroll
        self.res_canvas.bind("<Enter>",
            lambda e: self.res_canvas.bind_all("<MouseWheel>",
                lambda ev: self.res_canvas.yview_scroll(-1*(ev.delta//120), "units")))
        self.res_canvas.bind("<Leave>",
            lambda e: self.res_canvas.unbind_all("<MouseWheel>"))

        # Placeholder
        self.placeholder = tk.Label(self.res_inner,
            text="\n\n🩺\n\nYour detailed health report\nwill appear here after scanning.\n\n"
                 "Steps:\n1. Start the camera\n2. Look straight at the screen\n3. Click 'Scan My Face'",
            font=("Segoe UI",10), bg=BG, fg=TXT3, justify=tk.CENTER)
        self.placeholder.pack(pady=30)

    # ── Helper: add a metric card ──────────────────────
    def _metric_card(self, parent, icon, title, items, score=None, score_color=GREEN):
        card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill=tk.X, pady=(0,5))

        hdr = tk.Frame(card, bg=BG_ELEVATED)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"  {icon}  {title}", font=("Segoe UI",10,"bold"),
                 bg=BG_ELEVATED, fg=TXT, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X,
                                                              padx=10, pady=5)
        if score is not None:
            tk.Label(hdr, text=f"{score}%", font=("Segoe UI",10,"bold"),
                     bg=BG_ELEVATED, fg=score_color).pack(side=tk.RIGHT, padx=10)

        for label, value, color in items:
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(row, text=label, font=("Segoe UI",9), bg=BG_CARD,
                     fg=TXT2, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=str(value), font=("Segoe UI",9,"bold"),
                     bg=BG_CARD, fg=color, anchor=tk.E).pack(side=tk.RIGHT)

        if score is not None:
            pb = ProgressBar(card, width=356, height=5)
            pb.pack(padx=12, pady=(2,8))
            pb.set(score, score_color)
        else:
            tk.Frame(card, bg=BG_CARD, height=6).pack()

    def _sc(self, v):
        if v >= 75: return GREEN
        if v >= 50: return YELLOW
        return RED

    # ── Camera controls ────────────────────────────────
    def _toggle_cam(self):
        if self.running:
            self._stop_cam()
        else:
            self._start_cam()

    def _start_cam(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error",
                "Could not open webcam.\nPlease check your camera connection.")
            return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.running = True
        self.btn_cam.config(text="⏹  Stop Camera", bg=RED, activebackground="#d03030")
        self.btn_scan.config(state=tk.NORMAL)
        self.status_dot.config(fg=GREEN)
        self.status_lbl.config(text="Live")
        self.canvas.delete("welcome")
        self._update()

    def _stop_cam(self):
        self.running = False
        if self.cap: self.cap.release(); self.cap = None
        self.btn_cam.config(text="▶  Start Camera", bg=ACCENT, activebackground="#4090e0")
        self.btn_scan.config(state=tk.DISABLED)
        self.status_dot.config(fg=RED)
        self.status_lbl.config(text="Camera Off")
        self.canvas.delete("all")
        self._show_welcome()

    def _update(self):
        if not self.running or not self.cap: return
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(30, self._update); return

        frame = cv2.flip(frame, 1)
        self.current_frame = frame.copy()

        # FPS
        now = time.time()
        dt = now - self.last_t; self.last_t = now
        if dt > 0: self.fps_q.append(1/dt)
        if self.fps_q:
            self.fps_lbl.config(text=f"{sum(self.fps_q)/len(self.fps_q):.0f} FPS")

        # Draw face boxes
        faces, _ = self.analyzer.detect_faces(frame)
        for (x,y,w,h) in faces:
            # Corner markers instead of full rectangle
            l = int(min(w,h)*0.15)
            c = (88,166,255)
            t = 2
            cv2.line(frame,(x,y),(x+l,y),c,t)
            cv2.line(frame,(x,y),(x,y+l),c,t)
            cv2.line(frame,(x+w,y),(x+w-l,y),c,t)
            cv2.line(frame,(x+w,y),(x+w,y+l),c,t)
            cv2.line(frame,(x,y+h),(x+l,y+h),c,t)
            cv2.line(frame,(x,y+h),(x,y+h-l),c,t)
            cv2.line(frame,(x+w,y+h),(x+w-l,y+h),c,t)
            cv2.line(frame,(x+w,y+h),(x+w,y+h-l),c,t)
            cv2.putText(frame,"Face Detected",(x,y-8),
                        cv2.FONT_HERSHEY_SIMPLEX,0.5,c,1,cv2.LINE_AA)

        # Auto scan
        if self.auto_var.get() and hasattr(self,'_afc'):
            self._afc += 1
            if self._afc >= 90:
                self._afc = 0; self._analyze()
        elif self.auto_var.get():
            self._afc = 0

        # Render
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw > 1 and ch > 1:
            # Maintain aspect ratio
            scale = min(cw / img.width, ch / img.height)
            nw, nh = int(img.width * scale), int(img.height * scale)
            img = img.resize((nw, nh), Image.LANCZOS)

        self._photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        ox = (cw - img.width) // 2
        oy = (ch - img.height) // 2
        self.canvas.create_image(ox, oy, anchor=tk.NW, image=self._photo)

        self.root.after(30, self._update)

    def _toggle_auto(self):
        self._afc = 0

    # ── Analysis ───────────────────────────────────────
    def _analyze(self):
        if self.current_frame is None: return
        self.status_lbl.config(text="Analyzing...")
        self.status_dot.config(fg=YELLOW)
        self.root.update_idletasks()

        r = self.analyzer.analyze(self.current_frame)
        if r is None:
            self.verdict_lbl.config(text="No face found", fg=ORANGE)
            self.emoji_lbl.config(text="🫣")
            self.score_lbl.config(text="Make sure your face is clearly visible")
            self.status_dot.config(fg=GREEN)
            self.status_lbl.config(text="Live")
            return

        self.result = r
        self.history.append(r)
        self.btn_report.config(state=tk.NORMAL)
        self._render_results(r)
        self.status_dot.config(fg=GREEN)
        self.status_lbl.config(text="Live")

    def _render_results(self, r):
        # Verdict
        self.emoji_lbl.config(text=r["emoji"])
        self.verdict_lbl.config(text=r["verdict"], fg=r["verdict_color"])
        self.score_lbl.config(text=f"Overall health score: {r['overall']} / 100")
        self.score_bar.set(r["overall"], self._sc(r["overall"]))

        # Clear details
        for w in self.res_inner.winfo_children():
            w.destroy()

        # Conditions
        ccard = tk.Frame(self.res_inner, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        ccard.pack(fill=tk.X, pady=(0,5))
        chdr = tk.Frame(ccard, bg=BG_ELEVATED)
        chdr.pack(fill=tk.X)
        tk.Label(chdr, text="  ⚠  Findings", font=("Segoe UI",10,"bold"),
                 bg=BG_ELEVATED, fg=TXT, anchor=tk.W).pack(fill=tk.X, padx=10, pady=5)
        for txt, desc, col in r["conditions"]:
            rf = tk.Frame(ccard, bg=BG_CARD)
            rf.pack(fill=tk.X, padx=12, pady=3)
            tk.Label(rf, text="●", font=("Segoe UI",7), bg=BG_CARD, fg=col).pack(side=tk.LEFT, padx=(0,6))
            cf = tk.Frame(rf, bg=BG_CARD)
            cf.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(cf, text=txt, font=("Segoe UI",9,"bold"), bg=BG_CARD, fg=col, anchor=tk.W).pack(anchor=tk.W)
            tk.Label(cf, text=desc, font=("Segoe UI",8), bg=BG_CARD, fg=TXT2, anchor=tk.W).pack(anchor=tk.W)
        tk.Frame(ccard, bg=BG_CARD, height=6).pack()

        # Skin
        sk = r["skin"]
        self._metric_card(self.res_inner, "🩺", "Skin Analysis", [
            ("Status", sk["status"], self._sc(sk["score"])),
            ("Concern", sk["concern"], TXT2),
            ("Redness Level", sk["redness"], TXT),
            ("Color Uniformity", f"{sk['uniformity']}%", self._sc(sk["uniformity"])),
            ("Cheek Symmetry", f"{sk['symmetry']}%", self._sc(sk["symmetry"])),
        ], sk["score"], self._sc(sk["score"]))

        # Eyes
        ey = r["eyes"]
        self._metric_card(self.res_inner, "👁️", "Eye Health", [
            ("Status", ey["status"], self._sc(ey["score"])),
            ("Concern", ey["concern"], TXT2),
            ("Redness Index", ey["redness"], TXT),
            ("Dark Circles", ey["dark_circles"],
             ORANGE if ey["dark_circles"]=="Visible" else GREEN),
        ], ey["score"], self._sc(ey["score"]))

        # Eye Closure & Blink
        ec = r["eye_closure"]
        closure_sc = max(0, 100 - ec["closure_pct"])
        self._metric_card(self.res_inner, "😑", "Eye Closure & Alertness", [
            ("Eye Closure", f"{ec['closure_pct']}%",
             GREEN if ec['closure_pct']<30 else (YELLOW if ec['closure_pct']<60 else RED)),
            ("Eye Openness", f"{ec['openness']}%",
             self._sc(ec['openness'])),
            ("Lid Status", ec["droop_status"],
             GREEN if "Wide" in ec["droop_status"] else (YELLOW if "Partial" in ec["droop_status"] else RED)),
            ("Blink Rate", f"{ec['blink_rate']} /min",
             GREEN if 10<=ec['blink_rate']<=25 else YELLOW),
            ("Eye Aspect Ratio", ec["ear"], TXT3),
        ], closure_sc, self._sc(closure_sc))

        # Stress Level
        st = r["stress"]
        stress_display = 100 - st["stress_score"]  # invert: higher bar = less stress = better
        self._metric_card(self.res_inner, "🧠", "Stress Level", [
            ("Level", st["level"], st["color"]),
            ("Stress Score", f"{st['stress_score']}%", st["color"]),
            ("Assessment", st["concern"], TXT2),
        ] + [(f[0], f"{'▓'*int(f[1]/10)}{'░'*(10-int(f[1]/10))}",
              RED if f[1]>=60 else (YELLOW if f[1]>=35 else GREEN))
             for f in st["factors"]],
            stress_display, self._sc(stress_display))

        # Texture
        tx = r["texture"]
        self._metric_card(self.res_inner, "🔬", "Skin Texture", [
            ("Status", tx["status"], self._sc(tx["score"])),
            ("Detail", tx["concern"], TXT2),
        ], tx["score"], self._sc(tx["score"]))

        # Shape
        sh = r["shape"]
        self._metric_card(self.res_inner, "📐", "Face Proportions", [
            ("Shape", sh["note"], TXT),
            ("Swelling Check", sh["swelling"],
             GREEN if "None" in sh["swelling"] else ORANGE),
            ("Aspect Ratio", sh["ratio"], TXT3),
        ])

        # Tips
        if r["tips"]:
            tcard = tk.Frame(self.res_inner, bg="#0d2818", highlightbackground="#1a4028",
                              highlightthickness=1)
            tcard.pack(fill=tk.X, pady=(5,5))
            tk.Label(tcard, text="  💡  Recommendations", font=("Segoe UI",10,"bold"),
                     bg="#132d1b", fg=GREEN, anchor=tk.W).pack(fill=tk.X, padx=10, pady=5)
            for tip in r["tips"][:5]:
                tk.Label(tcard, text=tip, font=("Segoe UI",9), bg="#0d2818",
                         fg="#8ed6a0", anchor=tk.W, wraplength=340,
                         justify=tk.LEFT).pack(padx=14, pady=2, anchor=tk.W)
            tk.Frame(tcard, bg="#0d2818", height=8).pack()

        # Meta
        tk.Label(self.res_inner, text=f"Scanned at {r['time']}  •  {r['date']}",
                 font=("Segoe UI",8), bg=BG, fg=TXT3).pack(pady=(8,2))
        tk.Label(self.res_inner,
                 text="⚠ For educational purposes only. Not a medical diagnosis.\nConsult a healthcare professional for real concerns.",
                 font=("Segoe UI",8), bg=BG, fg=TXT3, justify=tk.CENTER).pack(pady=(0,15))

    # ── HTML Report ────────────────────────────────────
    def _export(self):
        if not self.result:
            messagebox.showinfo("No Data", "Run a scan first before exporting.")
            return
        r = self.result
        sc = r["overall"]
        vc = r["verdict_color"]

        conds_html = ""
        for t, d, c in r["conditions"]:
            conds_html += f'<div class="cond"><span class="dot" style="color:{c}">●</span><div><strong style="color:{c}">{t}</strong><br><span class="sub">{d}</span></div></div>'

        def bar(v):
            c = GREEN if v>=75 else (YELLOW if v>=50 else RED)
            return f'<div class="bar-track"><div class="bar-fill" style="width:{v}%;background:{c}"></div></div>'

        tips_html = "".join(f"<li>{t}</li>" for t in r["tips"][:6])

        html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Health Report — {r['date']}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#0d1117;color:#e6edf3;padding:40px 20px}}
.wrap{{max-width:720px;margin:0 auto}}
.header{{text-align:center;margin-bottom:32px}}
.header h1{{font-size:28px;color:#58a6ff;margin-bottom:4px}}
.header p{{color:#8b949e;font-size:13px}}
.verdict-box{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:28px;text-align:center;margin-bottom:20px}}
.verdict-box .emoji{{font-size:48px}}
.verdict-box h2{{font-size:26px;color:{vc};margin:8px 0 4px}}
.verdict-box .score{{color:#8b949e;font-size:15px}}
.bar-track{{background:#21262d;border-radius:6px;height:10px;margin:10px auto;max-width:320px}}
.bar-fill{{height:100%;border-radius:6px;transition:width .3s}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:10px;margin-bottom:14px;overflow:hidden}}
.card-hdr{{background:#1c2333;padding:10px 16px;font-weight:600;font-size:14px}}
.card-body{{padding:12px 16px}}
.row{{display:flex;justify-content:space-between;padding:4px 0;font-size:13px}}
.row .lbl{{color:#8b949e}}.row .val{{font-weight:600}}
.cond{{display:flex;align-items:flex-start;gap:8px;padding:6px 0}}
.cond .dot{{font-size:10px;margin-top:3px}}
.cond .sub{{color:#8b949e;font-size:12px}}
.tips{{background:#0d2818;border:1px solid #1a4028;border-radius:10px;padding:16px 20px;margin:16px 0}}
.tips h3{{color:#3fb950;font-size:14px;margin-bottom:10px}}
.tips li{{color:#8ed6a0;font-size:13px;margin-bottom:6px;margin-left:16px}}
.footer{{text-align:center;color:#484f58;font-size:11px;margin-top:24px;padding-top:16px;border-top:1px solid #21262d}}
</style></head><body><div class="wrap">
<div class="header"><h1>🩺 Face Health Report</h1><p>{r['date']} at {r['time']}</p></div>
<div class="verdict-box"><div class="emoji">{r['emoji']}</div><h2>{r['verdict']}</h2>
<div class="score">Overall Health Score: {sc} / 100</div>{bar(sc)}</div>
<div class="card"><div class="card-hdr">⚠ Findings</div><div class="card-body">{conds_html}</div></div>
<div class="card"><div class="card-hdr">🩺 Skin Analysis — {r['skin']['score']}%</div><div class="card-body">
<div class="row"><span class="lbl">Status</span><span class="val">{r['skin']['status']}</span></div>
<div class="row"><span class="lbl">Detail</span><span class="val" style="color:#8b949e">{r['skin']['concern']}</span></div>
<div class="row"><span class="lbl">Redness</span><span class="val">{r['skin']['redness']}</span></div>
<div class="row"><span class="lbl">Uniformity</span><span class="val">{r['skin']['uniformity']}%</span></div>
<div class="row"><span class="lbl">Symmetry</span><span class="val">{r['skin']['symmetry']}%</span></div>
{bar(r['skin']['score'])}</div></div>
<div class="card"><div class="card-hdr">👁️ Eye Health — {r['eyes']['score']}%</div><div class="card-body">
<div class="row"><span class="lbl">Status</span><span class="val">{r['eyes']['status']}</span></div>
<div class="row"><span class="lbl">Detail</span><span class="val" style="color:#8b949e">{r['eyes']['concern']}</span></div>
<div class="row"><span class="lbl">Redness Index</span><span class="val">{r['eyes']['redness']}</span></div>
<div class="row"><span class="lbl">Dark Circles</span><span class="val">{r['eyes']['dark_circles']}</span></div>
{bar(r['eyes']['score'])}</div></div>
<div class="card"><div class="card-hdr">🔬 Skin Texture — {r['texture']['score']}%</div><div class="card-body">
<div class="row"><span class="lbl">Status</span><span class="val">{r['texture']['status']}</span></div>
<div class="row"><span class="lbl">Detail</span><span class="val" style="color:#8b949e">{r['texture']['concern']}</span></div>
{bar(r['texture']['score'])}</div></div>
<div class="card"><div class="card-hdr">📐 Face Proportions</div><div class="card-body">
<div class="row"><span class="lbl">Shape</span><span class="val">{r['shape']['note']}</span></div>
<div class="row"><span class="lbl">Swelling Check</span><span class="val">{r['shape']['swelling']}</span></div>
<div class="row"><span class="lbl">Aspect Ratio</span><span class="val">{r['shape']['ratio']}</span></div></div></div>
<div class="card"><div class="card-hdr">😑 Eye Closure & Alertness — {100-r['eye_closure']['closure_pct']}%</div><div class="card-body">
<div class="row"><span class="lbl">Eye Closure</span><span class="val">{r['eye_closure']['closure_pct']}%</span></div>
<div class="row"><span class="lbl">Eye Openness</span><span class="val">{r['eye_closure']['openness']}%</span></div>
<div class="row"><span class="lbl">Lid Status</span><span class="val">{r['eye_closure']['droop_status']}</span></div>
<div class="row"><span class="lbl">Blink Rate</span><span class="val">{r['eye_closure']['blink_rate']} /min</span></div>
<div class="row"><span class="lbl">Eye Aspect Ratio</span><span class="val">{r['eye_closure']['ear']}</span></div>
{bar(100-r['eye_closure']['closure_pct'])}</div></div>
<div class="card"><div class="card-hdr">🧠 Stress Level — {r['stress']['level']}</div><div class="card-body">
<div class="row"><span class="lbl">Stress Score</span><span class="val" style="color:{r['stress']['color']}">{r['stress']['stress_score']}%</span></div>
<div class="row"><span class="lbl">Assessment</span><span class="val" style="color:#8b949e">{r['stress']['concern']}</span></div>
{bar(100-r['stress']['stress_score'])}</div></div>
<div class="tips"><h3>💡 Personalized Recommendations</h3><ul>{tips_html}</ul></div>
<div class="footer">⚠ This report is for educational/informational purposes only.<br>
It is NOT a medical diagnosis. Please consult a healthcare professional for real health concerns.<br><br>
Generated by Face Health Analyzer • {r['date']}</div></div></body></html>"""

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open(f"file:///{path.replace(os.sep, '/')}")
        self.status_lbl.config(text="Report exported!")
        self.root.after(3000, lambda: self.status_lbl.config(
            text="Live" if self.running else "Camera Off"))

    def _quit(self):
        self._stop_cam()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
