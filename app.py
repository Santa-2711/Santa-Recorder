import os, sys, subprocess, shutil, time
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QFileDialog, QMessageBox)

APP_NAME = "SANTA RECORDER"

def ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")

class Recorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.proc = None
        self.started = None
        self.target = None
        self.folder = str(Path.home() / "Videos")
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(640, 650)
        self.setStyleSheet("""
            QMainWindow, QWidget { background:#111018; color:#f5f2fa; font-family:Segoe UI; }
            QLabel#muted { color:#aaa4b8; }
            QComboBox { background:#211b2b; border:1px solid #49365d; border-radius:8px; padding:10px; color:white; }
            QPushButton { background:#30223f; border:1px solid #60477b; border-radius:10px; padding:12px; color:white; font-weight:600; }
            QPushButton#record { background:#7c3aed; border:0; }
            QPushButton#shot { background:#155e75; border:0; }
            QPushButton:disabled { color:#777; background:#29232f; }
            QCheckBox { spacing:10px; }
        """)
        root=QWidget(); self.setCentralWidget(root)
        layout=QVBoxLayout(root); layout.setContentsMargins(28,24,28,24); layout.setSpacing(14)
        brand=QLabel("SANTA RECORDER"); brand.setStyleSheet("font-size:25px;font-weight:800;color:#c4a5ff;")
        layout.addWidget(brand)
        subtitle=QLabel("Captura de pantalla, video y audio para Windows"); subtitle.setObjectName("muted"); layout.addWidget(subtitle)
        layout.addSpacing(6)
        layout.addWidget(self.label("CALIDAD DE VIDEO"))
        self.quality=QComboBox()
        self.quality.addItems(["Original (pantalla completa)","Full HD · 1920 × 1080","2K · 2560 × 1440","4K · 3840 × 2160"])
        layout.addWidget(self.quality)
        layout.addWidget(self.label("FPS"))
        self.fps=QComboBox(); self.fps.addItems(["30 FPS","60 FPS"]); layout.addWidget(self.fps)
        self.audio=QCheckBox("Grabar audio interno de Windows (WASAPI)")
        self.audio.setChecked(True); layout.addWidget(self.audio)
        self.out=QLabel("Guardar en: "+self.folder); self.out.setObjectName("muted"); self.out.setWordWrap(True); layout.addWidget(self.out)
        choose=QPushButton("Elegir carpeta de destino"); choose.clicked.connect(self.choose_folder); layout.addWidget(choose)
        self.status=QLabel("● LISTO PARA GRABAR"); self.status.setStyleSheet("color:#a78bfa;font-weight:700;")
        layout.addWidget(self.status)
        self.timer=QLabel("00:00:00"); self.timer.setStyleSheet("font-size:30px;font-weight:700;")
        layout.addWidget(self.timer)
        self.record=QPushButton("●  INICIAR GRABACIÓN"); self.record.setObjectName("record")
        self.record.clicked.connect(self.toggle); layout.addWidget(self.record)
        self.screenshot=QPushButton("▣  CAPTURAR PANTALLA (PNG)"); self.screenshot.setObjectName("shot")
        self.screenshot.clicked.connect(self.take_screenshot); layout.addWidget(self.screenshot)
        note=QLabel("La captura de pantalla guarda una imagen PNG. La resolución 4K depende de la pantalla y del rendimiento del equipo. Si el audio WASAPI no está disponible en FFmpeg, desactiva la casilla de audio.")
        note.setWordWrap(True); note.setObjectName("muted"); layout.addWidget(note)
        layout.addStretch()
        self.clock=QTimer(self); self.clock.timeout.connect(self.update_timer)
        self.setWindowIcon(QIcon(str(Path(__file__).parent/"assets"/"santa-recorder.ico")))

    def label(self,text):
        x=QLabel(text); x.setStyleSheet("font-size:11px;font-weight:700;color:#aaa4b8;"); return x

    def choose_folder(self):
        d=QFileDialog.getExistingDirectory(self,"Seleccionar carpeta",self.folder)
        if d: self.folder=d; self.out.setText("Guardar en: "+d)

    def take_screenshot(self):
        exe=ffmpeg_path()
        if not exe:
            QMessageBox.critical(self,"FFmpeg no encontrado","No se encontró FFmpeg.")
            return
        Path(self.folder).mkdir(parents=True,exist_ok=True)
        target=str(Path(self.folder)/("SantaRecorder_Captura_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".png"))
        args=[exe,"-y","-f","gdigrab","-i","desktop","-frames:v","1",target]
        try:
            result=subprocess.run(args,capture_output=True,text=True,timeout=30)
            if result.returncode != 0 or not Path(target).exists():
                details=(result.stderr or "FFmpeg no pudo crear la imagen.")[-1800:]
                QMessageBox.critical(self,"Error al capturar pantalla",details)
                return
            QMessageBox.information(self,"Captura guardada","La imagen PNG se guardó correctamente.")
            self.open_folder(target)
        except Exception as e:
            QMessageBox.critical(self,"Error al capturar pantalla",str(e))

    def toggle(self):
        if self.proc: self.stop(); return
        exe=ffmpeg_path()
        if not exe:
            QMessageBox.critical(self,"FFmpeg no encontrado","No se encontró FFmpeg.")
            return
        Path(self.folder).mkdir(parents=True,exist_ok=True)
        self.target=str(Path(self.folder)/("SantaRecorder_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".mp4"))
        fps="60" if self.fps.currentIndex()==1 else "30"
        args=[exe,"-y","-f","gdigrab","-framerate",fps,"-i","desktop"]
        if self.audio.isChecked():
            args += ["-f","wasapi","-i","default"]
        idx=self.quality.currentIndex()
        if idx:
            dims=["","1920:1080","2560:1440","3840:2160"][idx]
            args += ["-vf",f"scale={dims}:force_original_aspect_ratio=decrease"]
        args += ["-c:v","libx264","-preset","ultrafast","-crf","20","-pix_fmt","yuv420p"]
        if self.audio.isChecked(): args += ["-c:a","aac","-b:a","192k"]
        args += ["-movflags","+faststart",self.target]
        try:
            self.proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            time.sleep(1.2)
            if self.proc.poll() is not None:
                error=self.proc.stderr.read().decode("utf-8",errors="replace")[-2500:]
                self.proc=None
                QMessageBox.critical(self,"FFmpeg no pudo iniciar",error or "No se pudo iniciar la captura. Prueba desactivar el audio.")
                return
            self.started=time.time()
            self.record.setText("■  DETENER GRABACIÓN")
            self.status.setText("● GRABANDO"); self.status.setStyleSheet("color:#fb7185;font-weight:700;")
            self.quality.setEnabled(False); self.fps.setEnabled(False); self.audio.setEnabled(False)
            self.screenshot.setEnabled(False)
            self.clock.start(500)
        except Exception as e:
            QMessageBox.critical(self,"Error al iniciar",str(e)); self.proc=None

    def stop(self):
        p=self.proc
        target=self.target
        self.proc=None
        self.clock.stop()
        try:
            if p and p.poll() is None:
                p.stdin.write(b"q\n"); p.stdin.flush()
                p.wait(timeout=20)
        except Exception:
            if p:
                p.kill()
                p.wait()
        self.record.setText("●  INICIAR GRABACIÓN")
        self.status.setText("● GRABACIÓN FINALIZADA"); self.status.setStyleSheet("color:#a78bfa;font-weight:700;")
        self.timer.setText("00:00:00")
        self.quality.setEnabled(True); self.fps.setEnabled(True); self.audio.setEnabled(True)
        self.screenshot.setEnabled(True)
        if target and Path(target).exists() and Path(target).stat().st_size > 0:
            QMessageBox.information(self,"Grabación finalizada","El video se guardó correctamente. Se abrirá la carpeta de destino.")
            self.open_folder(target)
        else:
            QMessageBox.warning(self,"No se encontró el video","FFmpeg no generó un archivo de video válido. Prueba desactivar la opción de audio y vuelve a grabar.")

    def open_folder(self,path):
        try:
            if sys.platform=="win32":
                subprocess.Popen(["explorer","/select,",os.path.normpath(path)])
            else:
                subprocess.Popen(["xdg-open",str(Path(path).parent)])
        except Exception:
            pass

    def update_timer(self):
        if self.started:
            s=int(time.time()-self.started)
            self.timer.setText(f"{s//3600:02}:{(s%3600)//60:02}:{s%60:02}")

    def closeEvent(self,event):
        if self.proc: self.stop()
        event.accept()

if __name__=="__main__":
    app=QApplication(sys.argv)
    w=Recorder(); w.show()
    sys.exit(app.exec())
